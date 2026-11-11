-- Only for the disposable audit MySQL container, never a comparison/development DB.
USE stock_data_cache;
INSERT INTO stocks(ticker,name,info_json,last_info_update,data_last_update,last_split_date,last_split_ratio,splits_updated_at)
VALUES ('ZZTINY','Synthetic micro price',JSON_OBJECT('currency','USD'),'2023-02-11','2023-02-11',NULL,NULL,NULL),
       ('ZZSPLIT','Synthetic stale split cache',JSON_OBJECT('currency','USD'),'2023-02-11','2023-02-11','2023-01-20',2,'2023-02-11');
INSERT INTO daily_prices(stock_id,date,open,high,low,close,adj_close,volume,data_quality)
SELECT id,'2023-01-02',0.00001,0.00001,0.00001,0.00001,0.00001,1000000,'good' FROM stocks WHERE ticker='ZZTINY';
INSERT INTO daily_prices(stock_id,date,open,high,low,close,adj_close,volume,data_quality)
SELECT id,'2023-02-10',0.00003,0.00003,0.00003,0.00003,0.00003,1000000,'good' FROM stocks WHERE ticker='ZZTINY';
-- Model two cached ranges saved on opposite sides of a 2:1 split adjustment.
INSERT INTO daily_prices(stock_id,date,open,high,low,close,adj_close,volume,data_quality)
SELECT id,'2023-01-02',100,100,100,100,100,1000000,'suspicious' FROM stocks WHERE ticker='ZZSPLIT';
INSERT INTO daily_prices(stock_id,date,open,high,low,close,adj_close,volume,data_quality)
SELECT id,'2023-02-10',50,50,50,50,50,1000000,'suspicious' FROM stocks WHERE ticker='ZZSPLIT';
