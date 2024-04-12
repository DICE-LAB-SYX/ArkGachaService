from enum import StrEnum
from typing import Any

from msgspec import Struct, field

type PoolResult = "list[list[tuple[list[float], list[PoolWeightItem]]]]"


class RuleType(StrEnum):
    NEWBEE = "NEWBEE"
    NORMAL = "NORMAL"
    ATTAIN = "ATTAIN"
    CLASSIC_ATTAIN = "CLASSIC_ATTAIN"
    LINKAGE = "LINKAGE"
    SINGLE = "SINGLE"
    LIMITED = "LIMITED"
    CLASSIC = "CLASSIC"
    FESCLASSIC = "FESCLASSIC"


class LinkageRuleType(StrEnum):
    LINKAGE_R6_01 = "LINKAGE_R6_01"
    LINKAGE_MH_01 = "LINKAGE_MH_01"


class GachaPerAvail(Struct):
    rarityRank: int
    charIdList: list[str]
    totalPercent: float


class GachaAvailChar(Struct):
    perAvailList: list[GachaPerAvail]


class GachaPerChar(Struct):
    rarityRank: int
    charIdList: list[str]
    percent: float
    count: int


class GachaUpChar(Struct):
    perCharList: list[GachaPerChar]


class GachaWeightUpChar(Struct):
    rarityRank: int
    charId: str
    weight: int


class GachaObject(Struct):
    gachaObject: str
    type_: int = field(name="type")
    imageType: int
    param: str | None


class GachaGroupObject(Struct):
    groupType: int
    startIndex: int
    endIndex: int


class GachaDetailInfo(Struct):
    availCharInfo: GachaAvailChar
    upCharInfo: GachaUpChar | None
    weightUpCharInfoList: list[GachaWeightUpChar] | None
    limitedChar: list[str] | None
    gachaObjList: list[GachaObject]
    gachaObjGroups: list[GachaGroupObject] | None


class GachaDetailTable(Struct):
    details: dict[str, GachaDetailInfo]


class GachaDataLinkageTenGachaTkt(Struct):
    itemId: str
    endTime: int
    gachaPoolId: str


class GachaDataLimitTenGachaTkt(Struct):
    itemId: str
    endTime: int


class GachaDataFreeLimitGachaData(Struct):
    poolId: str
    openTime: int
    endTime: int
    freeCount: int


class GachaDataCarouselData(Struct):
    poolId: str
    index: int
    startTime: int
    endTime: int
    spriteId: str


class ItemBundle(Struct):
    id_: str = field(name="id")
    count: int
    type_: str = field(name="type")


class GachaDataRecruitRange(Struct):
    rarityStart: int
    rarityEnd: int


class PotentialMaterialConverterConfig(Struct):
    items: dict[str, ItemBundle]


class RecruitPoolRecruitTime(Struct):
    timeLength: int
    recruitPrice: int
    accumRate: float | None = None


class RecruitConstantsData(Struct):
    tagPriceList: dict[str, int]
    maxRecruitTime: int
    rarityWeights: None = None
    recruitTimeFactorList: None = None


class RecruitPool(Struct):
    recruitTimeTable: list[RecruitPoolRecruitTime]
    recruitConstants: RecruitConstantsData
    recruitCharacterList: None = None
    maskTypeWeightTable: None = None


class NewbeeGachaPoolClientData(Struct):
    gachaPoolId: str
    gachaIndex: int
    gachaPoolName: str
    gachaPoolDetail: str
    gachaPrice: int
    gachaTimes: int
    gachaOffset: str | None = None
    firstOpenDay: int | None = None
    reOpenDay: int | None = None
    gachaPoolItems: None = None
    signUpEarliestTime: int | None = None


class GachaPoolClientData(Struct):
    CDPrimColor: str | None
    CDSecColor: str | None
    endTime: int
    gachaIndex: int
    gachaPoolDetail: str | None
    gachaPoolId: str
    gachaPoolName: str
    gachaPoolSummary: str
    gachaRuleType: str
    guarantee5Avail: int
    guarantee5Count: int
    LMTGSID: str | None
    openTime: int
    dynMeta: dict[str, Any] | None = None
    linkageParam: dict[str, Any] | None = None
    linkageRuleId: str | None = None


class GachaTag(Struct):
    tagId: int
    tagName: str
    tagGroup: int


class SpecialRecruitPoolSpecialRecruitCostData(Struct):
    itemCosts: ItemBundle
    recruitPrice: int
    timeLength: int


class SpecialRecruitPool(Struct):
    endDateTime: int
    order: int
    recruitId: str
    recruitTimeTable: list[SpecialRecruitPoolSpecialRecruitCostData]
    startDateTime: int
    tagId: int
    tagName: str
    CDPrimColor: str | None
    CDSecColor: str | None
    LMTGSID: str | None
    gachaRuleType: str


class GachaDataFesGachaPoolRelateItem(Struct):
    rarityRank5ItemId: str
    rarityRank6ItemId: str


class GachaTable(Struct):
    __version__ = "24-03-29-14-33-44-5002d2"

    gachaTags: list[GachaTag]
    carousel: list[GachaDataCarouselData]
    classicPotentialMaterialConverter: PotentialMaterialConverterConfig
    dicRecruit6StarHint: dict[str, str] | None
    fesGachaPoolRelateItem: dict[str, GachaDataFesGachaPoolRelateItem] | None
    freeGacha: list[GachaDataFreeLimitGachaData]
    gachaPoolClient: list[GachaPoolClientData]
    limitTenGachaItem: list[GachaDataLimitTenGachaTkt]
    linkageTenGachaItem: list[GachaDataLinkageTenGachaTkt]
    newbeeGachaPoolClient: list[NewbeeGachaPoolClientData]
    potentialMaterialConverter: PotentialMaterialConverterConfig
    recruitDetail: str
    recruitPool: RecruitPool
    recruitRarityTable: dict[str, GachaDataRecruitRange]
    specialRecruitPool: list[SpecialRecruitPool]
    specialTagRarityTable: dict[str, list[int]]
    gachaTagMaxValid: int | None = None
    potentialMats: dict | None = None
    classicPotentialMats: dict | None = None


class PoolWeightItem(Struct):
    id_: str = field(name="id")
    count: int
    type_: str = field(name="type")
    rarity: int
    isClassic: bool = field(default=False)
    beforeNonHitCnt: int | None = field(default=None)
    singleEnsureCnt: int | None = field(default=None)
    isSingleEnsure: bool | None = field(default=None)

    def bulidLog(self) -> dict:
        m_log: dict[str, bool | int] = {}
        if self.beforeNonHitCnt is not None:
            m_log["beforeNonHitCnt"] = self.beforeNonHitCnt
        if self.singleEnsureCnt is not None:
            m_log["singleEnsureCnt"] = self.singleEnsureCnt
        if self.isSingleEnsure is not None:
            m_log["isSingleEnsure"] = self.isSingleEnsure
        return m_log


class gachaGroupConfig(Struct):
    normalCharCnt: int
    weights: list[float] = field(default_factory=list)
    pool: list[PoolWeightItem] = field(default_factory=list)
    upChars_1: list[str] = field(default_factory=list)
    upChars_2: list[str] = field(default_factory=list)
    perUpWeight_1: float = field(default=0.0)
    perUpWeight_2: float = field(default=0.0)
    totalWeights: float = field(default=1.0)


class GachaPoolInfo(Struct, omit_defaults=False):
    init: int = field(default=0)
    totalCnt: int = field(default=0)
    non6StarCnt: int = field(default=0)
    non5StarCnt: int = field(default=0)
    gain5Star: list[str] = field(default_factory=list)
    gain6Star: list[str] = field(default_factory=list)
    history: list[str] = field(default_factory=list)


class GachaTrackModel(Struct, omit_defaults=False):
    pool: dict[str, GachaPoolInfo] = field(default_factory=dict)
    nonNormal6StarCnt: int = field(default=0)
    nonClassic6StarCnt: int = field(default=0)


class PlayerGacha(Struct):
    class PlayerNewbeeGachaPool(Struct):
        openFlag: int
        cnt: int
        poolId: str

    class PlayerGachaPool(Struct):
        cnt: int
        maxCnt: int
        rarity: int
        avail: bool

    class PlayerFreeLimitGacha(Struct):
        leastFree: int

    class PlayerLinkageGacha(Struct):
        next5: bool
        next5Char: str
        must6: bool
        must6Char: str
        must6Count: int
        must6Level: int

    class PlayerAttainGacha(Struct):
        attain6Count: int

    class PlayerSingleGacha(Struct):
        singleEnsureCnt: int
        singleEnsureUse: bool
        singleEnsureChar: str
        cnt: int | None = field(default=None)
        maxCnt: int | None = field(default=None)
        avail: bool | None = field(default=None)

    class PlayerFesClassicGacha(Struct):
        upChar: dict[str, list[str]]

    newbee: PlayerNewbeeGachaPool
    normal: dict[str, PlayerGachaPool]
    attain: dict[str, PlayerAttainGacha]
    single: dict[str, PlayerSingleGacha]
    fesClassic: dict[str, PlayerFesClassicGacha]
    limit: dict[str, PlayerFreeLimitGacha]
    linkage: dict[str, dict[str, PlayerLinkageGacha]]
