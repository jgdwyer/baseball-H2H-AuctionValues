from baseball import run

if __name__ == "__main__":
    U, meta = run.do_hitters()
    P, SP, RP = run.do_pitchers()
    run.write_to_file(U, meta, SP, RP)
