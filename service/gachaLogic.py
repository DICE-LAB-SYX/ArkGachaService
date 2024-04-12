import json
from pathlib import Path
import random
from typing import ClassVar

from .gachaTrigger import GachaTrigger
from .models import (
    GachaDetailTable,
    GachaPoolClientData,
    GachaPoolInfo,
    GachaTable,
    GachaTrackModel,
    LinkageRuleType,
    PlayerGacha,
    PoolWeightItem,
    RuleType,
)
from .poolGenerator import PoolGenerator

from loguru import logger
from msgspec import convert, json as mscjson


class GachaService:
    RIT5_UP_CNT_1: ClassVar[int] = 15
    RIT5_UP_CNT_2: ClassVar[int] = 20
    RIT6_UP_CNT: ClassVar[int] = 50

    forbiddenGachaPool: ClassVar[list[str]] = []

    def __init__(self, showLog: bool = True) -> None:
        self.showLog: bool = showLog
        self.data = PlayerGacha(
            newbee=PlayerGacha.PlayerNewbeeGachaPool(
                openFlag=1,
                cnt=21,
                poolId="BOOT_0_1_2"
            ),
            normal={},
            attain={},
            single={},
            fesClassic={},
            limit={},
            linkage={}
        )
        self.track = GachaTrackModel()

        with Path("gacha_table.json").open(encoding="UTF-8") as f:
            self.Excel = convert(json.load(f), GachaTable)
        with Path("gacha_detail_table.json").open(encoding="UTF-8") as f:
            self.Server = convert(json.load(f), GachaDetailTable)
        self.trigger: GachaTrigger = GachaTrigger(self.data, self.track)

    async def doAdvancedGacha(self, poolId: str, ruleType: str) -> PoolWeightItem:
        pool = self.Server.details[poolId]
        state = self._tryGetTrackState(poolId)

        guaranteed = await self._getGuaranteedRarity(poolId)
        rarityHit = self._getRarityHit(poolId, guaranteed)
        if "BOOT" in poolId and not state.totalCnt:
            rarityHit = 3

        if ruleType != RuleType.FESCLASSIC:
            gachaPool = await PoolGenerator.build(pool)
        else:
            gachaPool = await PoolGenerator.build(pool, poolId, self.data)

        weightPool = gachaPool[rarityHit]
        charHit = random.choices(weightPool[0][1], weights=weightPool[0][0], k=1)[0]
        charHit.beforeNonHitCnt = state.non6StarCnt

        if ruleType != RuleType.FESCLASSIC and pool.upCharInfo and pool.upCharInfo.perCharList:
            if state.totalCnt + 1 >= 60:
                perChar = pool.upCharInfo.perCharList[-1]
                if charHit.rarity == perChar.rarityRank == 4:
                    if charIdList := [c for c in perChar.charIdList if c not in state.gain5Star]:
                        charHit.id_ = random.choice(charIdList)
            if state.totalCnt + 1 >= 200:
                perChar = pool.upCharInfo.perCharList[0]
                if charHit.rarity == perChar.rarityRank == 5:
                    if charIdList := [c for c in perChar.charIdList if c not in state.gain6Star]:
                        charHit.id_ = random.choice(charIdList)
        await self.trigger.postAdvancedGacha(poolId, charHit)

        if charHit.rarity == 4:
            state.non5StarCnt = 0
            state.gain5Star.append(charHit.id_)
        if charHit.rarity == 5:
            state.non6StarCnt = state.non5StarCnt = 0
            state.gain6Star.append(charHit.id_)
        else:
            state.non5StarCnt += 1
            state.non6StarCnt += 1
        state.totalCnt += 1

        if self.showLog:
            logger.debug(f"{ruleType}|{poolId}: {mscjson.decode(mscjson.encode(charHit))}")
        return charHit

    async def handleNormalGacha(self, poolId: str, useTkt: int) -> PoolWeightItem:
        poolClient = next(p for p in self.Excel.gachaPoolClient if p.gachaPoolId == poolId)
        state = self._tryGetTrackState(poolId)

        if not state.init:
            if poolClient.gachaRuleType == RuleType.NORMAL:
                state.non6StarCnt = self.track.nonNormal6StarCnt
            state.init = 1

        ## === ↓ ***基础数据校验*** ↓ ===
        # poolClient.openTime <= now <= poolClient.endTime -> gacha pool not open
        # useTkt:1|TKT_GACHA -> useTkt:0|DIAMOND_SHD -> gacha tkt state error
        ## === ↑ ***基础数据校验*** ↑ ===

        return await self.doAdvancedGacha(poolId, poolClient.gachaRuleType)

    async def handleTenNormalGacha(self, poolId: str, itemId: str, useTkt: int) -> list[PoolWeightItem]:
        poolClient = next(p for p in self.Excel.gachaPoolClient if p.gachaPoolId == poolId)
        state = self._tryGetTrackState(poolId)

        if not state.init:
            if poolClient.gachaRuleType == RuleType.NORMAL:
                state.non6StarCnt = self.track.nonNormal6StarCnt
            state.init = 1

        ## === ↓ ***基础数据校验*** ↓ ===
        # poolClient.openTime <= now <= poolClient.endTime -> gacha pool not open
        # useTkt:4|LINKAGE_TKT_GACHA_10 -> useTkt:2|TKT_GACHA_10 -> useTkt:5|TKT_GACHA -> useTkt:0|DIAMOND_SHD -> gacha tkt state error
        ## === ↑ ***基础数据校验*** ↑ ===

        result: list[PoolWeightItem] = []
        for _ in range(10):
            obj = await self.doAdvancedGacha(poolId, poolClient.gachaRuleType)
            result.append(obj)
        return result

    async def handleNewbeeGacha(self, poolId: str) -> PoolWeightItem:
        poolClient = next(p for p in self.Excel.newbeeGachaPoolClient if p.gachaPoolId == poolId)
        carousel = next(g for g in self.Excel.carousel if g.poolId == poolId)
        curPool = self.data.newbee
        state = self._tryGetTrackState(poolId)

        if not state.init:
            state.init = 1

        ## === ↓ ***基础数据校验*** ↓ ===
        # carousel.startTime <= now <= carousel.endTime | openFlag -> gacha pool not open
        # cnt = 0 -> newbie pool cnt not enough
        ## === ↑ ***基础数据校验*** ↑ ===

        # 调试状态下模拟客户端请求时需强制完成`obt/guide/l0-0/1_recruit_adv`
        curPool.cnt -= 1

        return await self.doAdvancedGacha(poolId, RuleType.NEWBEE)

    async def handleTenNewbieGacha(self, poolId: str) -> list[PoolWeightItem]:
        poolClient = next(p for p in self.Excel.newbeeGachaPoolClient if p.gachaPoolId == poolId)
        carousel = next(g for g in self.Excel.carousel if g.poolId == poolId)
        curPool = self.data.newbee
        state = self._tryGetTrackState(poolId)

        if not state.init:
            state.init = 1

        ## === ↓ ***基础数据校验*** ↓ ===
        # carousel.startTime <= now <= carousel.endTime | openFlag -> gacha pool not open
        # cnt < 10 -> newbie pool cnt not enough
        ## === ↑ ***基础数据校验*** ↑ ===

        curPool.cnt -= 10

        result: list[PoolWeightItem] = []
        for _ in range(10):
            obj = await self.doAdvancedGacha(poolId, RuleType.NEWBEE)
            result.append(obj)
        return result

    async def handleLimitedGacha(self, poolId: str, useTkt: int) -> tuple[PoolWeightItem, list]:
        poolClient = next(p for p in self.Excel.gachaPoolClient if p.gachaPoolId == poolId)
        state = self._tryGetTrackState(poolId)
        itemGet = []

        if not state.init:
            state.init = 1

        ## === ↓ ***基础数据校验*** ↓ ===
        # poolClient.openTime <= now <= poolClient.endTime -> gacha pool not open
        # useTkt:3 -> useTkt:1|TKT_GACHA -> useTkt:0|DIAMOND_SHD -> gacha tkt state error
        ## === ↑ ***基础数据校验*** ↑ ===

        if useTkt == 3 and self.data.limit[poolId].leastFree:
            self.data.limit[poolId].leastFree -= 1
        # 处理 lmtgs -> itemGet

        return await self.doAdvancedGacha(poolId, poolClient.gachaRuleType), itemGet

    async def handleTenLimitedGacha(self, poolId: str, itemId: str, useTkt: int) -> tuple[list[PoolWeightItem], list[list]]:
        poolClient = next(p for p in self.Excel.gachaPoolClient if p.gachaPoolId == poolId)
        state = self._tryGetTrackState(poolId)
        itemGet = []

        if not state.init:
            state.init = 1

        ## === ↓ ***基础数据校验*** ↓ ===
        # poolClient.openTime <= now <= poolClient.endTime -> gacha pool not open
        # useTkt:4|LIMITED_TKT_GACHA_10 -> useTkt:2|TKT_GACHA_10 -> useTkt:5|TKT_GACHA -> useTkt:0|DIAMOND_SHD -> gacha tkt state error
        ## === ↑ ***基础数据校验*** ↑ ===

        # 处理 lmtgs -> itemGet
        result: list[PoolWeightItem] = []

        for _ in range(10):
            obj = await self.doAdvancedGacha(poolId, poolClient.gachaRuleType)
            result.append(obj)
        return result, itemGet

    async def handleClassicGacha(self, poolId: str, useTkt: int) -> PoolWeightItem:
        poolClient = next(p for p in self.Excel.gachaPoolClient if p.gachaPoolId == poolId)
        state = self._tryGetTrackState(poolId)

        if not state.init:
            state.init = 1

        ## === ↓ ***基础数据校验*** ↓ ===
        # poolClient.openTime <= now <= poolClient.endTime -> gacha pool not open
        # useTkt:6|CLASSIC_TKT_GACHA -> useTkt:1|TKT_GACHA -> useTkt:0|DIAMOND_SHD -> gacha tkt state error
        ## === ↑ ***基础数据校验*** ↑ ===

        return await self.doAdvancedGacha(poolId, poolClient.gachaRuleType)

    async def handleTenClassicGacha(self, poolId: str, useTkt: int) -> list[PoolWeightItem]:
        poolClient = next(p for p in self.Excel.gachaPoolClient if p.gachaPoolId == poolId)
        state = self._tryGetTrackState(poolId)

        if not state.init:
            state.init = 1

        ## === ↓ ***基础数据校验*** ↓ ===
        # poolClient.openTime <= now <= poolClient.endTime -> gacha pool not open
        # useTkt:7|CLASSIC_TKT_GACHA_10 -> useTkt:8|CLASSIC_TKT_GACHA -> useTkt:2|TKT_GACHA_10 -> useTkt:5|TKT_GACHA -> useTkt:0|DIAMOND_SHD -> gacha tkt state error
        ## === ↑ ***基础数据校验*** ↑ ===

        result: list[PoolWeightItem] = []
        for _ in range(10):
            obj = await self.doAdvancedGacha(poolId, poolClient.gachaRuleType)
            result.append(obj)
        return result

    async def tryInitGachaRule(self, poolClient: GachaPoolClientData) -> None:
        poolId = poolClient.gachaPoolId
        match poolClient.gachaRuleType:
            case RuleType.ATTAIN | RuleType.CLASSIC_ATTAIN:
                await self._initAttainPoolState(poolId, poolClient)
            case RuleType.LINKAGE:
                await self._initLinkagePoolState(poolId, poolClient)
            case RuleType.SINGLE:
                await self._initSinglePoolState(poolId)
            case RuleType.FESCLASSIC:
                await self._initFesClassicPoolState(poolId)

    def _tryGetTrackState(self, poolId: str) -> GachaPoolInfo:
        self.track.pool.setdefault(poolId, GachaPoolInfo())
        return self.track.pool[poolId]

    async def _initAttainPoolState(self, poolId: str, poolClient: GachaPoolClientData) -> None:
        attain6Count = (poolClient.dynMeta or {}).get("attainRare6Num", 0)
        poolObj = self.data.PlayerAttainGacha(attain6Count=attain6Count)
        self.data.attain.setdefault(poolId, poolObj)

    async def _initLinkagePoolState(self, poolId: str, poolClient: GachaPoolClientData) -> None:
        pool = self.Server.details[poolId]
        if (upCharInfo := pool.upCharInfo) and poolClient.linkageParam:
            match rType := poolClient.linkageRuleId:
                case LinkageRuleType.LINKAGE_R6_01:
                    poolObj = self.data.PlayerLinkageGacha(
                        next5=True,
                        next5Char="",
                        must6=True,
                        must6Char=upCharInfo.perCharList[0].charIdList[0],
                        must6Count=poolClient.linkageParam["guaranteeTarget6Count"],
                        must6Level=5
                    )
                case LinkageRuleType.LINKAGE_MH_01:
                    poolObj = self.data.PlayerLinkageGacha(
                        next5=False,
                        next5Char="",
                        must6=True,
                        must6Char=upCharInfo.perCharList[0].charIdList[0],
                        must6Count=poolClient.linkageParam["guaranteeTarget6Count"],
                        must6Level=5
                    )
                case _:
                    raise ValueError("invalid linkage gacha rule id")
            self.data.linkage.setdefault(rType, {})
            self.data.linkage[rType].setdefault(poolId, poolObj)

    async def _initSinglePoolState(self, poolId: str) -> None:
        pool = self.Server.details[poolId]
        if upCharInfo := pool.upCharInfo:
            poolObj = self.data.PlayerSingleGacha(
                singleEnsureCnt=0,
                singleEnsureUse=False,
                singleEnsureChar=upCharInfo.perCharList[0].charIdList[0]
            )
            self.data.single.setdefault(poolId, poolObj)

    async def _initFesClassicPoolState(self, poolId: str) -> None:
        poolObj = self.data.PlayerFesClassicGacha(upChar={})
        self.data.fesClassic.setdefault(poolId, poolObj)

    def _getRarityHit(self, poolId: str, guaranteed: int) -> int:
        pool = self.Server.details[poolId]
        perAvailList = pool.availCharInfo.perAvailList
        state = self._tryGetTrackState(poolId)
        rarityWeights = [0.0] * 2 + [i.totalPercent for i in reversed(perAvailList)]

        add6StarWeight = 0
        if state.non6StarCnt >= self.RIT6_UP_CNT:
            add6StarWeight += rarityWeights[5] * (1 + state.non6StarCnt - self.RIT6_UP_CNT)
            if rarityWeights[5] + add6StarWeight > 1:
                add6StarWeight = 1 - rarityWeights[5]
            rarityWeights[5] += add6StarWeight

        add5StarWeight = 0
        if (cnt51 := min(1 + state.non5StarCnt - self.RIT5_UP_CNT_1, 5)) > 0:
            add5StarWeight += rarityWeights[4] * cnt51 * 0.25
        if (cnt52 := 1 + state.non5StarCnt - self.RIT5_UP_CNT_2) >= 0:
            add5StarWeight += rarityWeights[4] * cnt52 * 0.5
        rarityWeights[4] += add5StarWeight

        totalWeight = 0
        for i in range(5, -1, -1):
            rarityWeights[i] = min(rarityWeights[i], 1 - totalWeight)
            totalWeight += rarityWeights[i]
        rarityWeights[2] = max(0, 1 - sum(rarityWeights[3:6]))

        rarityHit = random.choices(range(6), weights=rarityWeights, k=1)[0]
        return max(rarityHit, guaranteed)

    async def _getGuaranteedRarity(self, poolId: str) -> int:
        newbeeGachaIds = [p.gachaPoolId for p in self.Excel.newbeeGachaPoolClient]
        guaranteedRarity = 2
        if poolId not in newbeeGachaIds:
            poolClient = next(p for p in self.Excel.gachaPoolClient if p.gachaPoolId == poolId)
            if poolId not in self.data.normal:
                self.data.normal[poolId] = self.data.PlayerGachaPool(
                    cnt=0,
                    maxCnt=poolClient.guarantee5Count,
                    rarity=4,
                    avail=bool(poolClient.guarantee5Avail)
                )
            curPool = self.data.normal[poolId]
            if curPool.avail and curPool.cnt + 1 == curPool.maxCnt:
                guaranteedRarity = curPool.rarity
            await self.tryInitGachaRule(poolClient)
        else:
            cur = self.track.pool[poolId]
            if not cur.gain6Star and cur.totalCnt + 1 == 10:
                guaranteedRarity = 5
            if not cur.gain5Star and cur.totalCnt + 1 == 21:
                guaranteedRarity = 4
        return guaranteedRarity
