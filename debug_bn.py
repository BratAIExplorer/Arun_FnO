
def check_banknifty():
    print("Searching for BANKNIFTY in nfo_master.csv...")
    try:
        with open("nfo_master.csv", "r") as f:
            count = 0
            for line in f:
                if "BANKNIFTY" in line:
                    print(line.strip())
                    count += 1
                    if count >= 20:
                        break
    except Exception as e:
        print(e)

if __name__ == "__main__":
    check_banknifty()
