#coding=utf-8

chmap = {  
    '0':0,'1':1,'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,  
    'x':10,'X':10  
    }  
  
def ch_to_num(ch):  
    return chmap[ch]      
  
def verify_identity(s):
    try:
        char_list = list(s)  
        num_list = [ch_to_num(ch) for ch in char_list]  
        return verify_list(num_list)
    except Exception,e:
        return False
  
def verify_list(l):  
    sum = 0  
    for ii,n in enumerate(l):  
        i = 18-ii  
        weight = 2**(i-1) % 11  
        sum = (sum + n*weight) % 11  
    return sum==1

def jiaoyanma(s):
    s = str(s)
    shenfenzheng17 = s[0:17]
    if type(shenfenzheng17) == str:  
        seq = map(int,shenfenzheng17)  
    elif type(shenfenzheng17) in [list,tuple]:  
        seq = shenfenzheng17  
      
    t = [7,9,10,5,8,4,2,1,6,3,7,9,10,5,8,4,2]  
    s = sum(map(lambda x:x[0]*x[1],zip(t,map(int,seq))))  
    b = s % 11  
    bd={  
        0: '1',  
        1: '0',  
        2: 'x',  
        3: '9',  
        4: '8',  
        5: '7',  
        6: '6',  
        7: '5',  
        8: '4',  
        9: '3',  
       10: '2'  
    }  
    print shenfenzheng17
    print bd[b]
    print s[17]
    return str(bd[b]) == str(s[17])
        
def card_check(card_number):
    card_number = str(card_number)
    try:
        last_len = len(card_number)-1
        bank_info = card_number[:last_len]
        total_number = 0
        bank_info = bank_info[::-1]
        for i in range(len(bank_info)):
            if i % 2 == 0:
                new_data = int(bank_info[i]) * 2
                if len(str(new_data)) == 2:                
                    total_number = total_number + int(str(new_data)[0]) + int(str(new_data)[1])
                else:
                    total_number = total_number + new_data
            else:
                total_number = total_number + int(bank_info[i])
        if (total_number + int(card_number[last_len])) % 10 == 0:
            return True
        else:
            return False
    except Exception,e:
        return False
        
if __name__ == '__main__':
    print card_check('6225880109980772')
        