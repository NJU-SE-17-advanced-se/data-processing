import csv

aff_id_2_name_dict = {}

with open('aff_id_to_name.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        line_count += 1
        if(len(row) != 2):
            print(len(row))
        aff_id_2_name_dict[row[0]] = row[1]
    print(f'Processed {line_count} lines.')

def get_aff_clean_name_by_id(aff_id):
    if aff_id in aff_id_2_name_dict:
        return aff_id_2_name_dict[aff_id]
    else:
        return None
