
import sys,getopt


def print_logo():
    print("""
      ____ ___ _   _  ____ 
     |  _ \_ _| \ | |/ ___|
     | |_) | ||  \| | |    
     |  __/| || |\  | |___ 
     |_|  |___|_| \_|\____|                   
    """)
    print("usage: \n"
          "     pinc.py -h                  # View Help\n"
          "     pinc.py -f <data.fasta>     # Data Prediction\n")


if __name__ == '__main__':

    argv = sys.argv[1:]
    try:
        opts, args = getopt.getopt(argv, "hf:c:", ["ifile=", "ofile="])
        if len(argv)==0:
            print_logo()
            sys.exit(2)
    except getopt.GetoptError:
        print_logo()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print_logo()
            sys.exit()
        elif opt in ("-f", "--ifile"):
            # if "/" in arg:
            #     arg = arg.split("/")[-1]
            # source_path = arg.split('.')[0]
            source_path = arg
            if ".fasta" != source_path[-6:]:
                print_logo()
                print("ERROR: Incorrect file extensions")
                sys.exit(2)

    print(source_path)