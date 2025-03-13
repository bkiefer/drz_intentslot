'''
Create data sets from the base_data annotated data
'''

import sys

def read_in_file(fname):
    id2tags = dict()
    id2tokens = dict()
    with open(fname) as f:
        lines = f.readlines()[1:]
        for line in lines:
            splitted = line.split(',')
            id, tokens, tags = splitted
            id = int(id)
            id2tokens[id] = tokens.strip()
            id2tags[id] = tags.strip()
    return id2tokens, id2tags

def write_in_file(fname, id2tags_and_tokens, ids):
    with open(fname, 'w') as f:
        f.write('id,tokens,einheit_tags,auftrag_tags,mittel_tags,ziel_tags,weg_tags\n')
        for id in ids:
            if(len(id2tags_and_tokens[id]['tags'])!=5):
                print(id, id2tags_and_tokens[id]['tags'])
                sys.exit(5)
            f.write(str(id)+','+id2tags_and_tokens[id]['tokens']+','+','.join(id2tags_and_tokens[id]['tags'])+'\n')

def write_in_anno_file(fname, id2tags_and_tokens, anno, ids):
    with open(fname, 'w') as f:
        f.write('id,tokens,tags\n')
        for id in ids:
            if(len(id2tags_and_tokens[id]['tags'])!=5):
                print(id, id2tags_and_tokens[id]['tags'])
                sys.exit(5)
            f.write(str(id) + ',' + id2tags_and_tokens[id]['tokens'] + ','
                    + id2tags_and_tokens[id]['tags'][anno] + '\n')


id2tags_and_tokens = dict()
anno_types = ["einheit", "auftrag", "mittel", "ziel", "weg"]

for anno_type in anno_types:
    id2tokens, id2tags = read_in_file("base_data/all_samples_"+anno_type+".csv")
    for id in id2tokens:
        if not(id in id2tags_and_tokens):
            id2tags_and_tokens[id] = {'tokens':[], 'tags':[]}
            id2tags_and_tokens[id]['tokens'] = id2tokens[id]
            id2tags_and_tokens[id]['tags'] = []
        id2tags_and_tokens[id]['tags'].append(id2tags[id])
        assert(id2tags_and_tokens[id]['tokens'] == id2tokens[id])
for id in id2tags_and_tokens:
    assert(len(id2tags_and_tokens[id]['tags'])==5)
    print(id, id2tags_and_tokens[id])

ids = {"dev":[], "train":[], "test":[]}
all_ids = list(id2tags_and_tokens.keys())
ids["test"] = all_ids[:100]
ids["train"] = all_ids[100:307]
ids["dev"] = all_ids[307:]

dtypes = ["dev", "train", "test"]
for dtype in dtypes:
    print(dtype, len(ids[dtype]))
    out_fname = "all_samples_all-in-one_"+dtype+".csv"
    write_in_file(out_fname, id2tags_and_tokens, ids[dtype])
    for anno in range(len(anno_types)):
        write_in_anno_file(f'all_samples_{anno_types[anno]}_{dtype}.csv',
                           id2tags_and_tokens, anno, ids[dtype])
