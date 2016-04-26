def last_lines(filename, lines = 1):
    #print the last line(s) of a text file
    """
    Argument filename is the name of the file to print.
    Argument lines is the number of lines to print from last.
    """
    block_size = 1024
    block = ''
    nl_count = 0
    start = 0
    try:
        fsock = file(filename, 'rU')

        #seek to end
        fsock.seek(0, 2)
        #get seek position
        curpos = fsock.tell()
        while(curpos > 0): #while not BOF
            #seek ahead block_size+the length of last read block
            curpos -= (block_size + len(block));
            if curpos < 0: curpos = 0
            fsock.seek(curpos)
            #read to end
            block = fsock.read()
            nl_count = block.count('\n')
            #if read enough(more)
            if nl_count >= lines: break
        #get the exact start position
        for n in range(nl_count-lines+1):
            start = block.find('\n', start)+1 
        fsock.close()
    except Exception,e:
        return []        
    #print it out  
    return block[start:].split('\n')

if __name__ == '__main__':
    lines = last_lines('/opt/FeedService/log/service.log' , 500)
    print lines
    #line_list = lines.split('\n')
    #print type(line_list)
    #print line_list
    
    