import calc_sgp
import addcats
import calc_sgp_P as scorep
import pandas as pd

def do_hitters():
    df = addcats.add_hitters()
    # sgp_addends = [0, 0, 0, 0, 0, 0, 0, 0]
    sgp_addends = pd.DataFrame(data={'sAVG': 0, 'sOBP': 0, 'sSLG': 0, 'sHR': 0,
                                     'sR': 0, 'sRBI': 0, 'sSB': 0, 'sTB': 0}, index=[0])

    for i in range(5):
        df = calc_sgp.sgp_hitters(df, sgp_addends)
        meta = calc_sgp.addpos(df)
        sgp_addends, sgp_pos_addends, meta_ranked = calc_sgp.calc_pos_scarcity(sgp_addends, meta)
        print('Loop {:d}'.format(i))
        print(sgp_addends)
        print(sgp_pos_addends)
    out = calc_sgp.add_pos_sgp(meta, sgp_pos_addends)
    return out


def do_pitchers():
    sgp_addends = [0, 0, 0, 0, 0, 0, 0, 0]
    for i in range(10):
        scorep.calc_sgp_SPRP(sgp_addends)
        sgp_addends, sgp_thresh = scorep.normalize_SPRP(sgp_addends)
        print(sgp_thresh)
    scorep.reorder_cols()
