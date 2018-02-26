import pandas as pd
from baseball import sgp, prep

def do_hitters():
    df = prep.run('hitters')
    cat_offsets = pd.DataFrame(data={key: 0 for key in ['sAVG', 'sOBP', 'sSLG', 'sHR', 'sR', 'sRBI', 'sSB', 'sTB']},
                               index=[0])
    print(df.head())
    df.to_csv('./df.csv')
    cat_offsets.to_pickle('./cat.p')
    for i in range(5):
        print('Loop {:d}'.format(i))
        df = sgp.calcSGPHitters(df, cat_offsets)
        cat_offsets, pos_offsets, star_thresh = sgp.calcPositionOffsets(cat_offsets, df)
    print('Thresholds for each category. Should be small:{}'.format(star_thresh))
    print('Offsets in each category:{}'.format(cat_offsets))
    print('Offsets at each position:{}'.format(pos_offsets))
    U, meta = sgp.addPositions(df, pos_offsets)
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
    P, SP, RP = sgp.reorder_cols(P)
    P.to_csv('./output/P.csv', index=False)
    SP.to_csv('./output/SP.csv', index=False)
    RP.to_csv('./output/RP.csv', index=False)
    return P, SP, RP


def write_to_file(U, meta, SP, RP):
    output_file = "./output/dc_2_16_2018.xlsx"
    # Parse files
    writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
    U.to_excel(writer, sheet_name='U')
    SP.to_excel(writer, sheet_name='SP')
    RP.to_excel(writer, sheet_name='RP')
    for key, _ in meta.items():
        meta[key].to_excel(writer, sheet_name=key)
    writer.save()
