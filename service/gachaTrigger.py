import json
from pathlib import Path
import random

from .models import (
    GachaDetailTable,
    GachaPoolInfo,
    GachaTable,
    GachaTrackModel,
    LinkageRuleType,
    PlayerGacha,
    PoolWeightItem,
    RuleType,
)
from .poolGenerator import PoolGenerator

from msgspec import convert


class GachaTrigger:
    def __init__(self, player_data: PlayerGacha, track: GachaTrackModel) -> None:
        self.data: PlayerGacha = player_data
        self.track: GachaTrackModel = track

        with Path("gacha_table.json").open(encoding="UTF-8") as f:
            self.Excel = convert(json.load(f), GachaTable)
        with Path("gacha_detail_table.json").open(encoding="UTF-8") as f:
            self.Server = convert(json.load(f), GachaDetailTable)

    async def postAdvancedGacha(self, poolId: str, charHit: PoolWeightItem) -> None:
        if poolId not in [p.gachaPoolId for p in self.Excel.newbeeGachaPoolClient]:
            poolClient = next(p for p in self.Excel.gachaPoolClient if p.gachaPoolId == poolId)
            match poolClient.gachaRuleType:
                case RuleType.LINKAGE:
                    await self._trigLinkageType(poolId, charHit)
                case RuleType.NORMAL:
                    await self._trigNoramlType(poolId)
                case RuleType.ATTAIN:
                    await self._trigAttainType(poolId, charHit)
                case RuleType.CLASSIC:
                    await self._trigClassicType(poolId, charHit)
                case RuleType.SINGLE:
                    await self._trigSingleType(poolId, charHit)
                case RuleType.FESCLASSIC:
                    await self._trigFesClassicType(poolId, charHit)
                case RuleType.CLASSIC_ATTAIN:
                    await self._trigClassicAttainType(poolId, charHit)

            curPool = self.data.normal[poolId]
            curPool.cnt += 1
            if curPool.avail and charHit.rarity >= curPool.rarity:
                curPool.avail = False

    def _tryGetTrackState(self, poolId: str) -> GachaPoolInfo:
        self.track.pool.setdefault(poolId, GachaPoolInfo())
        return self.track.pool[poolId]

    async def _trigLinkageType(self, poolId: str, charHit: PoolWeightItem) -> None:
        pool = self.Server.details[poolId]
        poolClient = next(p for p in self.Excel.gachaPoolClient if p.gachaPoolId == poolId)
        state = self._tryGetTrackState(poolId)

        if not (linkageGroup := self.data.linkage):
            return
        if not(upCharInfo := pool.upCharInfo):
            return
        match rType := poolClient.linkageRuleId:
            case LinkageRuleType.LINKAGE_R6_01:
                level5CharIdList = upCharInfo.perCharList[-1].charIdList
                linkage = linkageGroup[poolId][rType]
                if linkage.must6:
                    linkage.must6Count -= 1
                    if linkage.must6Count <= 0:
                        charHit.id_ = linkage.must6Char
                        charHit.rarity = linkage.must6Level
                if charHit.rarity == 5 and charHit.id_ == linkage.must6Char:
                    linkage.must6 = False
                    linkage.must6Char = ""
                    linkage.must6Count = 0
                if charHit.rarity == 4 and charHit.id_ in level5CharIdList:
                    if linkage.next5 and linkage.next5Char != "":
                        charHit.id_ = linkage.next5Char
                    if charHit.id_ in level5CharIdList:
                        if next5Chars := [c for c in level5CharIdList if c not in state.gain5Star]:
                            linkage.next5Char = next5Chars[0]
                        else:
                            linkage.next5 = False
                            linkage.next5Char = ""
            case LinkageRuleType.LINKAGE_MH_01:
                linkage = linkageGroup[poolId][rType]
                if linkage.must6:
                    linkage.must6Count -= 1
                    if linkage.must6Count <= 0:
                        charHit.id_ = linkage.must6Char
                        charHit.rarity = linkage.must6Level
                if charHit.rarity == 5 and charHit.id_ == linkage.must6Char:
                    linkage.must6 = False
                    linkage.must6Char = ""
                    linkage.must6Count = 0
            case _:
                raise ValueError("invalid linkage pool rule type")

    async def _trigNoramlType(self, poolId: str) -> None:
        state = self._tryGetTrackState(poolId)
        self.track.nonNormal6StarCnt = state.non6StarCnt

    async def _trigAttainType(self, poolId: str, charHit: PoolWeightItem) -> None:
        pool = self.Server.details[poolId]
        weightPool = await PoolGenerator.build(pool)
        attain = self.data.attain[poolId]
        # userChars = player_data.user.troop.chars 开源版本仅供参考演示

        if not attain.attain6Count or charHit.rarity != 5:
            return
        attainPool = []
        for item in weightPool[charHit.rarity][0][1]:
            # if any(c.charId == item.id_ for c in userChars.values()):
            #     continue
            attainPool.append(item.id_)
        if attainPool:
            charHit.id_ = random.choice(attainPool)
        attain.attain6Count -= 1

    async def _trigClassicType(self, poolId: str, charHit: PoolWeightItem) -> None:
        state = self._tryGetTrackState(poolId)
        self.track.nonClassic6StarCnt = state.non6StarCnt
        charHit.isClassic = True

    async def _trigSingleType(self, poolId: str, charHit: PoolWeightItem) -> None:
        pool = self.Server.details[poolId]
        single = self.data.single[poolId]
        charHit.singleEnsureCnt = 150 if single.singleEnsureCnt < 0 else single.singleEnsureCnt
        charHit.isSingleEnsure = False

        if single.singleEnsureUse or not pool.upCharInfo:
            return
        must6Char = pool.upCharInfo.perCharList[0].charIdList[0]
        if single.singleEnsureCnt >= 0:
            if single.singleEnsureCnt + 1 < 150:
                if charHit.id_ != must6Char:
                    single.singleEnsureCnt += 1
                else:
                    single.singleEnsureCnt = 0
            elif charHit.id_ != must6Char:
                single.singleEnsureCnt -= 1
            else:
                single.singleEnsureCnt = 0
        elif charHit.rarity == 5:
            charHit.id_ = single.singleEnsureChar
            single.singleEnsureUse = True
            charHit.isSingleEnsure = True

    async def _trigFesClassicType(self, poolId: str, charHit: PoolWeightItem) -> None:
        state = self._tryGetTrackState(poolId)
        self.track.nonClassic6StarCnt = state.non6StarCnt
        charHit.isClassic = True

    async def _trigClassicAttainType(self, poolId: str, charHit: PoolWeightItem) -> None:
        pool = self.Server.details[poolId]
        weightPool = await PoolGenerator.build(pool)
        attain = self.data.attain[poolId]
        # userChars = player_data.user.troop.chars 开源版本仅供参考演示
        charHit.isClassic = True

        if not attain.attain6Count or charHit.rarity != 5:
            return
        attainPool = []
        for item in weightPool[charHit.rarity][0][1]:
            # if any(c.charId == item.id_ for c in userChars.values()):
            #     continue
            attainPool.append(item.id_)
        if attainPool:
            charHit.id_ = random.choice(attainPool)
        attain.attain6Count -= 1
