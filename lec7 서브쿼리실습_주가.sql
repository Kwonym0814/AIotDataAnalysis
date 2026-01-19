
select distinct tname as 종목명
    from kospi
    order by tname asc ;
    
select to_char(min(rdate),'yyyy-mm-dd') as 시작일, to_char(max(rdate),'yyyy-mm-dd') as 종료일
    from kospi;
    
--총 투자 기간
    
select round((max(rdate) - min(rdate))/30) as "투자기간(개월)"
    from kospi;
    
select months_between(max(rdate),min(rdate)) as "투자기간(개월)"
    from kospi;

select tname, max(cprice), min(cprice)
    from kospi
    group by tname
    order by tname asc;

select k.tname, k.cprice, k.rdate
 from kospi k
 join (select tname, max(rdate)as mxd
    from kospi group by tname) mx on k.rdate = mx.mxd and k.tname = mx.tname
    ;
    
select k.tname, k.cprice, k.rdate
 from kospi k
 where (k.tname, k.rdate) in (select tname, max(rdate)
    from kospi group by tname);    
    
select tname, gubun, count(1) as CNT
    from (select tname, case when oprice < cprice then '상승'
                             when oprice > cprice then '하락'
                                                  else '보합' end as gubun
            from kospi)
    group by tname, gubun
    order by tname asc;

select u.tname, u.gubun1, u.CNT1, d.gubun2, d.CNT2
    from (select tname, '상승' as gubun1, count(case when oprice < cprice then '상승' end) as CNT1 from kospi group by tname) u
    join (select tname, '하락' as gubun2, count(case when oprice >= cprice then '하락' end) as CNT2 from kospi group by tname) d
    on u.tname = d.tname
    order by u.tname;
    
select tname, extract(year from rdate) as year, extract(month from rdate) as month, to_char(sum(vol), '999,999,999') as trade_amount
    from kospi
    where tname = '카카오' and rdate >=to_date('2022-01-01', 'yyyy-mm-dd') and rdate <to_date('2023-01-01', 'yyyy-mm-dd')
    group by tname, extract(year from rdate), extract(month from rdate)
    order by year, month;
    
    
    
with tmp as (select tname, extract(year from rdate) as year, extract(month from rdate) as month, sum(vol) as trade_amount
            from kospi
            where tname = '카카오' 
            and rdate >=to_date('2022-01-01', 'yyyy-mm-dd') and rdate <to_date('2023-01-01', 'yyyy-mm-dd')
            group by tname, extract(year from rdate), extract(month from rdate))
    select year, month, trade_amount
    from tmp 
    where trade_amount = (select max(trade_amount) from tmp)
    ;


SELECT 
      MAX(EXTRACT(YEAR FROM rdate))  KEEP (DENSE_RANK LAST ORDER BY SUM(vol)) AS year
    , MAX(EXTRACT(MONTH FROM rdate)) KEEP (DENSE_RANK LAST ORDER BY SUM(vol)) AS month
    , MAX(SUM(vol)) AS max_trade_amount
FROM kospi
WHERE tname = '카카오'
GROUP BY EXTRACT(YEAR FROM rdate), EXTRACT(MONTH FROM rdate)
ORDER BY max_trade_amount DESC
FETCH FIRST 1 ROWS ONLY;