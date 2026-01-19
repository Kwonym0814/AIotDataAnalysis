
--7. 전체 회원 목록 중 휴면 회원이 차지하는 비율?
--조건1 : 관리자 제외
--조건2: 휴면회원은 구매 실적이 전혀 없는 회원
-- 회원수   휴면회원비율
--------- 
--  1/4      25%

with sleep as (select count(user_seq) from users where user_seq not in (select distinct user_seq from orders))
    , tot as (select count(user_seq) from users where user_id != 'admin')
select (select * from sleep) || '/' || (select * from tot) as 회원수
   ,round((select * from sleep)/(select * from tot)*100,2) || '%' as 휴면회원비율
from dual; 



select (b.cnt_u - b.cnt_o)||'/'||(b.cnt_u) as 회원수
    ,(b.cnt_u - b.cnt_o)/b.cnt_u*100 || '%' as 휴면회원비율
from (select count(u.user_seq) as cnt_u, count(o.user_seq)as cnt_o
    from users u
    left join (select distinct user_seq from orders) o on u.user_seq = o.user_seq
    where u.user_id != 'admin') b;

with sleep as (select count(user_seq) from users where user_seq not in (select distinct user_seq from orders))
    , tot as (select count(user_seq) from users where user_id != 'admin')
select (select * from sleep) || '/' || (select * from tot) as 회원수
   ,round((select * from sleep)/(select * from tot)*100,2) || '%' as 휴면회원비율
from dual; 

--8. 각 회원별로 매니저-회원 관계를 출력하시오
--조건1: 관리자 제외
--조건2: 매니저번호 오름차순 회원번호 오름차순 정렬

select coalesce(m.user_id,'없음') as mgr_id, u.user_id as user_id
    from users u
    left join users m on u.mgr_seq = m.user_seq
    where u.user_gubun != 'a'
     order by mgr_id asc, user_id asc ;
     
select nvl(m.user_id,'없음') as mgr_id, u.user_id as user_id
    from users u
    left join users m on u.mgr_seq = m.user_seq
    where u.user_gubun != 'a'
     order by mgr_id asc, user_id asc ;

select nvl2(m.user_id,m.user_id,'없음') as mgr_id, u.user_id as user_id
    from users u
    left join users m on u.mgr_seq = m.user_seq
    where u.user_gubun != 'a'
     order by mgr_id asc, user_id asc ;


with grade as (select deptno, case when sal < 1000 then 'a'
                   when sal < 2000 then 'b'
                                else 'c' end as salgrade                                            
    from emp)
select deptno, count(salgrade)
from grade
group by deptno
order by deptno
    ;
    
with ee as (select to_char(hiredate, 'mm') as hm, sum(sal) as ssal
            from emp
            group by to_char(hiredate, 'mm'))
 select (select ssal from ee where hm = '01') as "01"
    , (select ssal from ee where hm = '02') as "02"
    , (select ssal from ee where hm = '03') as "03"
    , (select ssal from ee where hm = '04') as "04"
    , (select ssal from ee where hm = '05') as "05"
    , (select ssal from ee where hm = '06') as "06"
    , (select ssal from ee where hm = '07') as "07"
    , (select ssal from ee where hm = '08') as "08"
    , (select ssal from ee where hm = '09') as "09"
    , (select ssal from ee where hm = '10') as "10"
    , (select ssal from ee where hm = '11') as "11"
    , (select ssal from ee where hm = '12') as "12"
    from dual;
    

with ee as (select to_char(hiredate, 'mm') as hm, sum(sal) as ssal
            from emp
            group by to_char(hiredate, 'mm'))
 select (select ssal from ee where hm = '01') as "01"
    , (select ssal from ee where hm = '02') as "02"
    , (select ssal from ee where hm = '03') as "03"
    , (select ssal from ee where hm = '04') as "04"
    , (select ssal from ee where hm = '05') as "05"
    , (select ssal from ee where hm = '06') as "06"
    , (select ssal from ee where hm = '07') as "07"
    , (select ssal from ee where hm = '08') as "08"
    , (select ssal from ee where hm = '09') as "09"
    , (select ssal from ee where hm = '10') as "10"
    , (select ssal from ee where hm = '11') as "11"
    , (select ssal from ee where hm = '12') as "12"
    from dual;
    
    
    select (select ssal from (select to_char(hiredate, 'mm') as hm, sum(sal) as ssal
            from emp
            group by to_char(hiredate, 'mm')) where hm = '01') as "01"
    , (select ssal from (select to_char(hiredate, 'mm') as hm, sum(sal) as ssal
            from emp
            group by to_char(hiredate, 'mm')) where hm = '02') as "02"
    , (select ssal from (select to_char(hiredate, 'mm') as hm, sum(sal) as ssal
            from emp
            group by to_char(hiredate, 'mm')) where hm = '03') as "03"
    , (select ssal from (select to_char(hiredate, 'mm') as hm, sum(sal) as ssal
            from emp
            group by to_char(hiredate, 'mm')) where hm = '04') as "04"
    , (select ssal from (select to_char(hiredate, 'mm') as hm, sum(sal) as ssal
            from emp
            group by to_char(hiredate, 'mm')) where hm = '05') as "05"
    , (select ssal from (select to_char(hiredate, 'mm') as hm, sum(sal) as ssal
            from emp
            group by to_char(hiredate, 'mm')) where hm = '06') as "06"
    , (select ssal from (select to_char(hiredate, 'mm') as hm, sum(sal) as ssal
            from emp
            group by to_char(hiredate, 'mm')) where hm = '07') as "07"
    , (select ssal from (select to_char(hiredate, 'mm') as hm, sum(sal) as ssal
            from emp
            group by to_char(hiredate, 'mm')) where hm = '08') as "08"
    , (select ssal from (select to_char(hiredate, 'mm') as hm, sum(sal) as ssal
            from emp
            group by to_char(hiredate, 'mm')) where hm = '09') as "09"
    , (select ssal from (select to_char(hiredate, 'mm') as hm, sum(sal) as ssal
            from emp
            group by to_char(hiredate, 'mm')) where hm = '10') as "10"
    , (select ssal from (select to_char(hiredate, 'mm') as hm, sum(sal) as ssal
            from emp
            group by to_char(hiredate, 'mm')) where hm = '11') as "11"
    , (select ssal from (select to_char(hiredate, 'mm') as hm, sum(sal) as ssal
            from emp
            group by to_char(hiredate, 'mm')) where hm = '12') as "12"
    from dual;
            
select deptno, count(1)
from emp
group by deptno;

select deptno
        ,coalesce(sum(case when to_char(hiredate, 'mm') = '01' then sal end),0) as "01"
        ,coalesce(sum(case when to_char(hiredate, 'mm') = '02' then sal end),0) as "02"
        ,coalesce(sum(case when to_char(hiredate, 'mm') = '03' then sal end),0) as "03"
        ,coalesce(sum(case when to_char(hiredate, 'mm') = '04' then sal end),0) as "04"
        ,coalesce(sum(case when to_char(hiredate, 'mm') = '05' then sal end),0) as "05"
        ,coalesce(sum(case when to_char(hiredate, 'mm') = '06' then sal end),0) as "06"
        ,coalesce(sum(case when to_char(hiredate, 'mm') = '07' then sal end),0) as "07"
        ,coalesce(sum(case when to_char(hiredate, 'mm') = '08' then sal end),0) as "08"
        ,coalesce(sum(case when to_char(hiredate, 'mm') = '09' then sal end),0) as "09"
        ,coalesce(sum(case when to_char(hiredate, 'mm') = '10' then sal end),0) as "10"
        ,coalesce(sum(case when to_char(hiredate, 'mm') = '11' then sal end),0) as "11"
        ,coalesce(sum(case when to_char(hiredate, 'mm') = '12' then sal end),0) as "12"
    from emp
    group by deptno
         ;
         
select 
	 decode(to_char(hiredate, 'mm'),'01',sal) as "01"
    ,decode(to_char(hiredate, 'mm'),'02',sal) as "02"
    ,decode(to_char(hiredate, 'mm'),'03',sal) as "03"
    ,decode(to_char(hiredate, 'mm'),'04',sal) as "04"
    ,decode(to_char(hiredate, 'mm'),'05',sal) as "05"
    ,decode(to_char(hiredate, 'mm'),'06',sal) as "06"
    ,decode(to_char(hiredate, 'mm'),'07',sal) as "07"
    ,decode(to_char(hiredate, 'mm'),'08',sal) as "08"
    ,decode(to_char(hiredate, 'mm'),'09',sal) as "09"
    ,decode(to_char(hiredate, 'mm'),'10',sal) as "10"
    ,decode(to_char(hiredate, 'mm'),'11',sal) as "11"
    ,decode(to_char(hiredate, 'mm'),'12',sal) as "12"        
    from emp
         ;
         
select *
    from (select to_char(hiredate, 'mm') as hm, sum(sal) as ssal
            from emp
            group by to_char(hiredate, 'mm'))
pivot(
sum(coalesce(ssal,0)) for hm in ('01' as "01",
                '02' as "02",
                '03' as "03",
                '04' as "04",
                '05' as "05",
                '06' as "06",
                '07' as "07",
                '08' as "08",
                '09' as "09",
                '10' as "10",
                '11' as "11",
                '12' as "12")
)        ;
    
select * 
    from (select sal, to_char(hiredate, 'mm') as mm from emp)
pivot(
    sum(sal) for mm in ('01' as "01",
                '02' as "02",
                '03' as "03",
                '04' as "04",
                '05' as "05",
                '06' as "06",
                '07' as "07",
                '08' as "08",
                '09' as "09",
                '10' as "10",
                '11' as "11",
                '12' as "12")
);
    
 --9. 주문/상품/업체 대시보드 현황판
-- 총주문수량 총주문금액  총회원수  총업체수 총상품수
--       AMT      PRICE       UCNT       CCNT       GCNT
---------- ---------- ---------- ---------- ----------
--        48     244000          5          7         10
    
select
    (select sum(order_amount) from orders_goods) as amt,
    (select sum(tot_price)  from orders)as price,
    (select count(1)  from users)as ucnt,
    (select count(1) from company) as ccnt,
    (select count(1)  from goods)as gcnt
    from dual;
    
--10.월별 판매 실적....
--  1월   2월   3월   4월  
-- 20000  12000  50000


select coalesce(sum(case when month = '01' then tot_price end),0) as mon01
        ,coalesce(sum(case when month = '02' then tot_price end),0) as mon02
        ,coalesce(sum(case when month = '03' then tot_price end),0) as mon03
        ,coalesce(sum(case when month = '04' then tot_price end),0) as mon04
        ,coalesce(sum(case when month = '05' then tot_price end),0) as mon05
        ,coalesce(sum(case when month = '06' then tot_price end),0) as mon06
        ,coalesce(sum(case when month = '07' then tot_price end),0) as mon07
        ,coalesce(sum(case when month = '08' then tot_price end),0) as mon08
        ,coalesce(sum(case when month = '09' then tot_price end),0) as mon09
        ,coalesce(sum(case when month = '10' then tot_price end),0) as mon10
        ,coalesce(sum(case when month = '11' then tot_price end),0) as mon11
        ,coalesce(sum(case when month = '12' then tot_price end),0) as mon12
    from (select tot_price, to_char(order_date, 'mm') as month
            from orders
            )
    ;
    

