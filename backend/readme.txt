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
example:
http://127.0.0.1:8000/brand/time-compare/frequency?brand_name=huggies&granularity=month&time1=6&time2=7

sentiment analysis across time
http://127.0.0.1:8000/brand/time-compare/sentiment
parameter:
brand_name
granularity
time1
time2
