import sgp
import prep
import pandas as pd

def do_hitters():
    df = prep.run('hitters')
    # sgp_addends = [0, 0, 0, 0, 0, 0, 0, 0]
    cat_offsets = pd.DataFrame(data={'sAVG': 0, 'sOBP': 0, 'sSLG': 0, 'sHR': 0,
                                     'sR': 0, 'sRBI': 0, 'sSB': 0, 'sTB': 0}, index=[0])
    for i in range(5):
        print('Loop {:d}'.format(i))
        df = sgp.calcSGPHitters(df, cat_offsets)
        cat_offsets, pos_offsets, star_thresh = sgp.calcPositionOffsets(cat_offsets, df)
    print('Thresholds for each category. Should be small:{}'.format(star_thresh))
    print('Offsets in each category:{}'.format(cat_offsets))
    print('Offsets at each position:{}'.format(pos_offsets))
    U, meta = calc_sgp.addPositions(df, pos_offsets)
    return U, meta


def do_pitchers():
    df = prep.run('pitchers')
    SP, RP = prep.separate_SP_RP(df)
    cat_offsets = pd.DataFrame(data={'sERA': 0, 'sWHIP': 0, 'sIP/GS': 0, 'sSO/BB': 0,
                                     'sSO': 0, 'sW': 0, 'sSV': 0, 'sHLD': 0}, index=[0])
    for i in range(10):
        print('Loop {:d}'.format(i))
        SP, RP, P = sgp.calcSGPPitchers(cat_offsets, SP, RP)
        cat_offsets, sgp_thresh = sgp.normSGPPitchers(cat_offsets, SP, RP)
    print('Thresholds for each category. Should be small:{}'.format(sgp_thresh))
    print('Offsets in each category:{}'.format(cat_offsets))
    P, SP, RP = sgp.reorder_cols(P)# scorep.reorder_cols()
    return P, SP, RP


def write_to_file():
    output_file = "./output/dc_3_23_2017/"
    # Parse files
    parse.parse_csv('cbs_hitters.html')
    parse.parse_csv('cbs_pitchers.html')
    U, meta = do_hitters()
    P, SP, RP = do_pitchers()
    writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
    U.to_excel(writer, sheet_name='U')
    SP.to_excel(writer, sheet_name='SP')
    RP.to_excel(writer, sheet_name='RP')
    for key, _ in meta.items():
        meta[key].to_excel(writer, sheet_name=key)
    writer.save()
