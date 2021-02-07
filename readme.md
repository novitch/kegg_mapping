# 1 Split the functional table
```
perl format_table_for_kegg_enrichment.pl -query=[functional table] -dir_out= [repertory]
```

# 2 perform the enrichment
```
for i in $(cat [list of files created in step 1]);do python reconstructModule_v3.py -s $i -r results/ ;done
```

# 3 concatenate
```
perl concat_kegg_enrichment.pl -query=lr -output=konzo_module_enrichment.txt
```
