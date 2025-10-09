uvicorn backend.main:app --reload 
========Tab1=============
http://127.0.0.1:8000/keyword-frequency?
parameter is:
year=2025
month=6,  take from [1,12]
quarter=3,    take from [1,4]

http://127.0.0.1:8000/new-keyword-prediction

========Tab3===========
keyword frequency across time 
http://127.0.0.1:8000/brand/time-compare/frequency
parameter:
brand_name
granularity, select from ["year","month","quarter"]
time1, corresponding time integer
time2, corresponding time integer
year: just year
month:202505->May 2025
quarter: 20251-> first quarter in 2025
example:
http://127.0.0.1:8000/brand/time-compare/frequency?brand_name=huggies&granularity=month&time1=202506&time2=202507

same as sentiment 
http://127.0.0.1:8000/brand/time-compare/sentiment?brand_name=huggies&granularity=month&time1=202506&time2=202507

==============Tab4===============
share of voice
http://127.0.0.1:8000/category/share-of-voice

co-occurence
http://127.0.0.1:8000/category/consumer-perception?category_name=diaper

category name is ["formula milk", "diaper","hospital","weaning"]