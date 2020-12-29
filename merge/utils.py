import hashlib
import csv
import logging
from datetime import datetime

now = datetime.now()

current_time = now.strftime("%H:%M:%S")
print("Current Time =", current_time)
logging.basicConfig(filename='/home/leo/Desktop/ASE/data-processing/log/clean_aff_{}.log'.format(current_time),
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.DEBUG)
logging.info("Running utils")
logger = logging.getLogger('utils')

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


def hash_str(s):
    hl = hashlib.md5()  # 如果是同一个 md5 对象然后多次 update 则得到的结果不同
    hl.update(s.encode())
    return hl.hexdigest()


def encode_id(it, prefix):
    for record in it:
        if record.get('id') == None:
            continue
        record['id'] = hash_str(prefix + record['id'])
    return it

def solve_affiliation_name1(s):
    l=['Univ','Unniversity',"College","Montreal","Polytechnique Montréal","Research Center","Lab","Institute","Business Group","Microsoft","Oxford","Cambrihge","Cambridge","ETH"]
    ig={'Reliability and Trust, Centre For Security, Luxembourg, LUXEMBOURG':'Reliability and Trust, Centre For Security',
    'SAP HANA Cloud Computing, Systems Engineering, Belfast, United Kingdom':'SAP HANA Cloud Computing, Systems Engineering',
    'BMW Group Research, New Technologies, Innovations, Garching b. München, Germany':'BMW Group Research, New Technologies, Innovations',
    'Department of ECE, Virginia Tech, Blacksburg, VA, USA':'Department of ECE, Virginia Tech',
    'DEEDS Group, TU Darmstadt, Darmstadt, Germany':'DEEDS Group, TU Darmstadt'}
    if s in ig.keys():
        return ig[s];
    s=s.replace('，',",")
    strs=s.split(',')
    if len(strs)==1:
        return s
    res=''
    index=-1
    for cur in range(0,len(strs)):
         for i in l:
             if i in strs[cur] or len(strs[cur])>25:
                 index=cur;
    if index==-1:
        return strs[0]
    res=strs[0]
    for i in range(0,index):
        res=res+','+strs[i]
    return res


def solve_affiliation_name(s):
    """ change affiliation name
    s:要处理的机构名

    Returns:
        处理后的机构名
    """
    l = ['Univ', 'Unniversity', "College", "Montreal", "Polytechnique Montréal", "Research Center", "Lab",
         "Institute", "Business Group", "Microsoft", "Oxford", "Cambrihge", "Cambridge", "ETH", "UNLP"]
    ig = {'Reliability and Trust, Centre For Security, Luxembourg, LUXEMBOURG': 'Reliability and Trust, Centre For Security',
          'SAP HANA Cloud Computing, Systems Engineering, Belfast, United Kingdom': 'SAP HANA Cloud Computing, Systems Engineering',
          'BMW Group Research, New Technologies, Innovations, Garching b. München, Germany': 'BMW Group Research, New Technologies, Innovations',
          'Department of ECE, Virginia Tech, Blacksburg, VA, USA': 'Department of ECE, Virginia Tech',
          'DEEDS Group, TU Darmstadt, Darmstadt, Germany': 'DEEDS Group, TU Darmstadt',
          'Cybernet Systems, Japan / IBM Research, Japan': 'Cybernet Systems, Japan / IBM Research',
          'Department of ECE, Virginia Tech., Blacksburg, VA': 'Department of ECE, Virginia Tech Blacksburg,',
          'Dept. of Computer Science, Virginia Tech., Blacksburg, VA': 'Dept. of Computer Science, Virginia Tech.',
          'SafeRiver, Montrouge, France and UPMC, Paris, France': 'SafeRiver and UPMC',
          'UFCG, Brazil and UC Berkeley': 'UFCG and UC Berkeley',
          'NICTA, Sydney, Australia and UNSW, Sydney, Australia ': 'NICTA and UNSW',
          'Anhui University, Hefei, China and Swinburne University of Technology, Melbourne, Australia': 'Anhui University and Swinburne University of Technology',
          'East China University of Technology, Nanchang, China and Anhui University, Hefei, Anhui, China': 'East China University of Technology and Anhui University',
          'Anhui University, Hefei, Anhui, China and Swinburne University of Technology, Melbourne, Australia': 'Anhui University and Swinburne University of Technology'}
    st = ['Grammatech Inc., Ithaca', 'Department of ECE, Virginia Tech Blacksburg',
          'LIFIA, Facultad de Informática, UNLP and CONICET, La Plata, Argentina', 'Grid Computing Group, Yahoo', 'CNR-IASI, and CNR-ISTI']
    if s in ig.keys():
        return ig[s]
    for s1 in st:
        if s1 in s:
            return s1
    s = s.replace('，', ",")
    strs = s.split(',')
    if len(strs) == 1:
        return s
    res = ''
    index = -1
    for cur in range(0, len(strs)):
        for i in l:
            if i in strs[cur] or len(strs[cur]) > 25:
                index = cur
    if index == -1:
        # print(s+'           '+strs[0])
        return strs[0]
    res = strs[0]
    for i in range(1, index+1):
        res = res+','+strs[i]
    return res


def get_clean_name_by_name(name):
    """给定 name，给出 clean name
    """
    solved_name = solve_affiliation_name1(name)
    solved_id = hash_str(solved_name)
    result = get_aff_clean_name_by_id(solved_id)
    if result == None:
        logger.warning('name: "{}", solved_name: "{}", solved_id: "{}"'.format(name, solved_name, solved_id))
    return result
    
