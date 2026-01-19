--컬럼 조희
select * from emp;
select empno, ename, sal from emp;
select empno, ename, sal + deptno as income, sal+100 as aa from emp;

--별칭(alias)
--컬럼 : 컬럼 [as] 별칭
--테이블 : 테이블 별칭    # as 없음.

select e.empno as eno, e.ename as enm from emp e;

-- 가감산
-- 컬럼타입: 수치형, 날짜타입
select hiredate, hiredate+1 as h2, hiredate-1 as h3 from emp;

-- 합치기(||)
--컬럼타입: 글자
select ename || ' ' || job as call_name from emp;

--날짜
--오늘날짜 : sysdate, now() : mysql or mariaDB
select hiredate, to_char(hiredate, 'YYYY-MM-DD') as h2, to_date(to_char(hiredate, 'YYYY-MM-DD')) as h3 from emp;
select sysdate from dual;
select trunc((sysdate - hiredate +1)/365.15) as d_year from emp;

--타입캐스팅(포맷팅)
--날짜 --> 글자
--글짜 --> 날짜
select hiredate, to_char(hiredate, 'YYYY-MM-DD') as h2, to_date(to_char(hiredate, 'YYYY-MM-DD')) as h3 from emp;
--숫자 --> 글자
--to_char(): char 고정길이로
--to_varchar2(): char 고정길이로
create table tmp as select to_char(empno) as p_id from emp;  
select to_varchar(empno) as p_id from emp;

select sal, comm from emp;
select sal, comm, sal+comm as aa from emp;
select sal, comm, case when comm is null then sal
                        when comm is not null then sal+comm end as income from emp;
select sal, comm, case when comm is null then sal
                        else sal+comm end as income from emp;                        
                    
select * from emp where comm is null or comm<=0;
select * from emp where comm is not null and comm>0;
select * from emp where not(comm is null or comm<=0);

select sal, comm, nvl(comm, 0) + sal as income from emp;  
/*
NVL1.0가장 가벼움
CASE (ELSE 사용)1.2
CASE (ELSE 미사용)1.5
*/


create table test (
    eno number primary key,
    bonus number not null,
    sal number default 100,
    dno number
);

insert into test(eno) values(111);