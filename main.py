import asyncio
import json

from loguru import logger
# import matplotlib.pyplot as plt
from msgspec import json as mscjson
from service.gachaLogic import GachaService
from service.models import GachaPoolClientData, RuleType


async def testAdvancedGacha(
    tester: GachaService, poolId: str, useTkt: int = 0
) -> None:
    newbeeGachaPoolClient = tester.Excel.newbeeGachaPoolClient
    gachaPoolClient = tester.Excel.gachaPoolClient

    if poolId not in [p.gachaPoolId for p in newbeeGachaPoolClient]:
        if not (pool := next((p for p in gachaPoolClient if p.gachaPoolId == poolId), None)):
            raise ValueError("invalid gacha pool id")
    elif not (pool := next((p for p in newbeeGachaPoolClient if p.gachaPoolId == poolId), None)):
        raise ValueError("invalid gacha pool id")

    if poolId in tester.forbiddenGachaPool:
        raise ValueError("当前寻访暂时无法使用, 详情请关注官方公告")

    if isinstance(pool, GachaPoolClientData):
        match pool.gachaRuleType:
            case RuleType.ATTAIN | RuleType.FESCLASSIC | RuleType.CLASSIC_ATTAIN:
                raise ValueError("开源版本仅做演示, 该类型卡池请自行完善")
            case RuleType.NORMAL | RuleType.SINGLE | RuleType.LINKAGE:
                result = await tester.handleNormalGacha(poolId, useTkt)
            case RuleType.LIMITED:
                result, itemGet = await tester.handleLimitedGacha(poolId, useTkt)
            case RuleType.CLASSIC:
                result = await tester.handleClassicGacha(poolId, useTkt)
            case _:
                raise ValueError(f"invalid gacha rule type: {pool.gachaRuleType}")
    else:
        result = await tester.handleNewbeeGacha(poolId)

    state = tester.track.pool[poolId]
    state.history.append(f"{result.id_}&{result.rarity}") # &{now}&{charGet.isNew}")


async def testTenAdvancedGacha(
    tester: GachaService, poolId: str, useTkt: int = 0, itemId: str = "4003"
) -> None:
    newbeeGachaPoolClient = tester.Excel.newbeeGachaPoolClient
    gachaPoolClient = tester.Excel.gachaPoolClient

    if poolId not in [p.gachaPoolId for p in newbeeGachaPoolClient]:
        if not (pool := next((p for p in gachaPoolClient if p.gachaPoolId == poolId), None)):
            raise ValueError("invalid gacha pool id")
    elif not (pool := next((p for p in newbeeGachaPoolClient if p.gachaPoolId == poolId), None)):
        raise ValueError("invalid gacha pool id")

    if poolId in tester.forbiddenGachaPool:
        raise ValueError("当前寻访暂时无法使用, 详情请关注官方公告")

    if isinstance(pool, GachaPoolClientData):
        match pool.gachaRuleType:
            case RuleType.ATTAIN | RuleType.FESCLASSIC | RuleType.CLASSIC_ATTAIN:
                raise ValueError("开源版本仅做演示, 该类型卡池请自行完善")
            case RuleType.NORMAL | RuleType.SINGLE | RuleType.LINKAGE:
                result = await tester.handleTenNormalGacha(poolId, itemId, useTkt)
            case RuleType.LIMITED:
                result, itemGet = await tester.handleTenLimitedGacha(poolId, itemId, useTkt)
            case RuleType.CLASSIC:
                result = await tester.handleTenClassicGacha(poolId, useTkt)
            case _:
                raise ValueError(f"invalid gacha rule type: {pool.gachaRuleType}")
    else:
        result = await tester.handleTenNewbieGacha(poolId)

    state = tester.track.pool[poolId]
    for _, bundle in enumerate(result):
        state.history.append(f"{bundle.id_}&{bundle.rarity}") # &{now}&{charGet.isNew}")


def gachaLogUserData(tester: GachaService) -> None:
    logger.debug(f"- PlayerData -\n{json.dumps(mscjson.decode(mscjson.encode(tester.data)), indent=2)}")
    logger.debug(f"- PlayerTrack -\n{json.dumps(mscjson.decode(mscjson.encode(tester.track)), indent=2)}")


async def testGachaService() -> None:
    for _ in range(10):
        await testAdvancedGacha(tester, "SINGLE_45_0_7", 0)
    for _ in range(5):
        await testTenAdvancedGacha(tester, "SINGLE_45_0_7", 0)
    gachaLogUserData(tester)
    # await buildExpectCt("SINGLE_45_0_7", ["char_4117_ray"])


if __name__ == "__main__":
    tester = GachaService()
    asyncio.run(testGachaService())
