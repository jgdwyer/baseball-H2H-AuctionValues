import calc_sgp
import addcats
import pandas as pd
import parse
from subprocess import call #for calling mkdir

def do_hitters():
    parse.parse_csv('cbs_hitters.html')
    df = addcats.prepHitters()
    df = addcats.addcbs_info(df, 'hitters')
    # sgp_addends = [0, 0, 0, 0, 0, 0, 0, 0]
    sgp_addends = pd.DataFrame(data={'sAVG': 0, 'sOBP': 0, 'sSLG': 0, 'sHR': 0,
                                     'sR': 0, 'sRBI': 0, 'sSB': 0, 'sTB': 0}, index=[0])

    for i in range(5):
        df = calc_sgp.sgp_hitters(df, sgp_addends)
        sgp_addends, sgp_pos_addends = calc_sgp.calc_pos_scarcity(sgp_addends, df)
        print('Loop {:d}'.format(i))
        print(sgp_addends)
        print(sgp_pos_addends)
    U, meta = calc_sgp.add_pos_sgp(df, sgp_pos_addends)
    return U, meta


def do_pitchers():
    df = addcats.add_pitchers()
    df = addcats.addcbs_info(df, 'pitchers')
    SP, RP, SPRP = addcats.separate_SP_RP(df)
    sgp_addends = pd.DataFrame(data={'sERA': 0, 'sWHIP': 0, 'sIP/GS': 0, 'sSO/BB': 0,
                                     'sSO': 0, 'sW': 0, 'sSV': 0, 'sHLD': 0}, index=[0])
    for i in range(10):
        SP, RP, P = calc_sgp.calc_sgp_SPRP(sgp_addends, SP, RP, SPRP)
        sgp_addends, sgp_thresh = calc_sgp.normalize_SPRP(sgp_addends, SP, RP)
        print(sgp_thresh)
    P, SP, RP = calc_sgp.reorder_cols(P)# scorep.reorder_cols()
    return P, SP, RP

def write_to_file():
    call(["mkdir", "-p", output_dir])
    # Parse files
    parse.parse_csv('cbs_hitters.html')
    parse.parse_csv('cbs_pitchers.html')
    U, meta = do_hitters()
    P, SP, RP = do_pitchers()
    writer = pd.ExcelWriter('jabo_3-22.xlsx', engine='xlsxwriter')
    U.to_excel(writer, sheet_name='U')
    SP.to_excel(writer, sheet_name='SP')
    RP.to_excel(writer, sheet_name='RP')
    for key, _ in meta.items():
        meta[key].to_excel(writer, sheet_name=key)
    writer.save()
