import calc_sgp as score

def do_hitters():
    sgp_addends = [0, 0, 0, 0, 0, 0, 0, 0]
    for i in range(10):
        score.sgp_hitters(sgp_addends)
        score.addpos()
        sgp_addends, sgp_pos_addends = score.calc_pos_scarcity(sgp_addends)
        print('Loop {}'.format(i))
        print(sgp_addends)
        print(sgp_pos_addends)
    score.add_pos_sgp(sgp_pos_addends)
