lines_to_ignore=(">","> ","- ","-")
chars_to_ignore=("*","`","|",'"',"_")
rp_indicators=('*','"','_')

def find_substring_indexes(desired_substring, message, index_type='start'): # returns index/es of substring
    array_of_indexes=[]
    # start the search at 0
    search_start_index=0
    while search_start_index < len(message):
        # look for the substring
        find_index=message[search_start_index:].find(desired_substring)
        # check if we found it
        if find_index!=-1:
            # if we found it, add it to our results
            # the index we find is relative to the start position, so we have to add it
            # append things depending on if we want last, first or all indexes. Defaults to start index
            if index_type=="end":
                # appends the last index of the substring
                array_of_indexes.append(find_index+search_start_index+len(desired_substring)-1)

            elif index_type=="all":
                # appends all indexes of the substring
                for char_in_substring in range(0, len(desired_substring)):
                    array_of_indexes.append(find_index+search_start_index+char_in_substring)
            else:
                # appends the starting index
                array_of_indexes.append(find_index+search_start_index)
            # set new start index
            search_start_index=search_start_index+find_index+len(desired_substring)
        else:
            # if not, break the search loop
            break
    return array_of_indexes

def check_pair_overlap(main_pair, secondary_pair): # checks the overlap of two pairs
    debug_mode=False
    # one is inside the other
    if secondary_pair[0] in range(main_pair[0], main_pair[1]) and secondary_pair[1] in range(main_pair[0], main_pair[1]): # sec inside main
        if debug_mode: print(f"{secondary_pair} is inside {main_pair}") 
        return 1
    elif main_pair[0] in range(secondary_pair[0], secondary_pair[1]) and main_pair[1] in range(secondary_pair[0], secondary_pair[1]): # main is inside sec
        if debug_mode: print(f"{main_pair} is inside {secondary_pair}") 
        return 2
    elif secondary_pair[0] in range(main_pair[0], main_pair[1]) : # sec starts in main
        if debug_mode: print(f"{secondary_pair} starts inside {main_pair}") 
        return 3
    elif secondary_pair[1] in range(main_pair[0], main_pair[1]) : # sec ends in main
        if debug_mode: print(f"{secondary_pair} ends inside {main_pair}") 
        return 4
    else: # they don't touch
        if debug_mode: print(f"{main_pair} doesn't overlap with {secondary_pair}")
        return False

def remove_redundant_pairs(valid_pairs): # returns a pair without redundant pairs
    # remove unfinished pairs
    for pair in valid_pairs:
        if len(pair)==1: valid_pairs.remove(pair)

    # remove overlapping pairs
    main_index=0
    while True: # loop as long as there's things to remove
        if main_index==len(valid_pairs): # if we're done removing, move to the next main pair
            break
        main_pair = valid_pairs[main_index] # get main pair
        sec_index=main_index+1 # set the start point for sec pairs

        while True: # loop through all the other pairs
            if sec_index==len(valid_pairs): # if we ran out of secondary pairs, move onto the next main pair
                break
            secondary_pair = valid_pairs[sec_index] # update secondary pair

            overlap=check_pair_overlap(main_pair, secondary_pair) # see overlap

            if overlap == 1: # sec is inside main
                valid_pairs.remove(secondary_pair) # yeet out the redundant pair
            elif overlap == 2: # main is inside sec
                valid_pairs.remove(secondary_pair) # yeet out the soon to be redundant pair
                main_pair=secondary_pair # expand the main pair
                valid_pairs[main_index]=main_pair # update list
                sec_index=main_index+1 # reset sec index
            elif overlap == 3: # sec starts in main
                valid_pairs.remove(secondary_pair) # yeet out the soon to be redundant pair
                main_pair=[main_pair[0], secondary_pair[1]] # expand the main pair
                valid_pairs[main_index]=main_pair # update list
                sec_index=main_index+1 # reset sec index
            elif overlap == 4: # main starts in sec
                valid_pairs.remove(secondary_pair) # yeet out the soon to be redundant pair
                main_pair=[secondary_pair[0], main_pair[1]] # expand the main pair
                valid_pairs[main_index]=main_pair # update list
                sec_index=main_index+1 # reset sec index
            else: # they don't overlap -> move onto the next pair to check against
                sec_index+=1

        main_index+=1 # move onto the next main pair

    return valid_pairs

def count(msg):
    # filter out non rp lines
    message=''
    for line in msg.split("\n"):
        if not line.startswith(lines_to_ignore) and line != '': message+=" "+line

    # Locate all the characters indicating rp
    indicator_indexes=[]
    for i,indicator in enumerate(rp_indicators):
        indicator_indexes.append(find_substring_indexes(indicator, message))
        # remove doubles of said characters
        for double in find_substring_indexes(indicator+indicator, message, "all"):
            indicator_indexes[i].remove(double)
    
    # Go through the rp indicators and split them into pairs
    valid_pairs=[]
    for indicator in indicator_indexes:
        valid_pairs.extend([indicator[i:i + 2] for i in range(0, len(indicator), 2)])
    
    # remove redundant pairs caused by overlap & any unfinished pairs
    valid_pairs=remove_redundant_pairs(valid_pairs)

    # clean up characters which should not count as words
    for char_to_rem in chars_to_ignore:
        message = message.replace(char_to_rem, " ")

    # Go through the valid segments of the original message and count the words inside them
    word_count=0
    for rp_pair in valid_pairs:
        rp_text=message[rp_pair[0]+1:rp_pair[1]]
        for word in rp_text.split(' '):
            if word != '':
                word_count+=1 # ignore empty words

    return word_count

    
