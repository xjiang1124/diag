import json

# Output
data1 = json.load(open('card_record.txt'))

f1= open("card_sn_die_id_all.csv","w+")
fmt_str = "{:15}{:15}{:50}"
fmt_str = "{},{},{}"
for card, sn_die_dict in data1.items():
    print(card)
    for sn, dieId in sn_die_dict.items():
        out_str = fmt_str.format(card, sn, dieId)
        #print out_str
        f1.write(out_str+'\n')
f1.close()
