select * from users;

insert into users values(9, 'park', 999);
select * from users;

update users set upw=888 where useq = 9;
select * from users;    

delete from users where useq = 9;
select * from users;    


insert, select, update, delete
--CRUD로 칭함


select empno, ename, comm, sal from emp where comm is null or comm <= 0 ;

select empno, ename, comm, sal, sal + nvl(comm,0) as income from emp;
select empno, ename, comm, sal, sal + coalesce(comm,0) as income from emp;

select empno, ename, comm, sal, deptno from emp where deptno = 10 OR deptno = 20 ;

select empno, ename, comm, sal, job, deptno from emp where deptno = 30 and job like 'SALESMAN' ;

select empno, ename, sal from emp where sal between 3000 and 5000;
select empno, ename, sal from emp where sal >= 3000 and sal <= 5000;
select empno, ename, sal from emp where 3000 <= sal  and sal <= 5000;


select empno, ename, comm, sal, deptno from emp where deptno in (10, 20);

select * from emp where job = 'CLERK' or job = 'MANAGER' or job = 'SALESMAN';
select * from emp where job in ('CLERK', 'MANAGER', 'SALESMAN');
select * from emp where job not in ('CLERK', 'MANAGER', 'SALESMAN');

select ename from emp where ename like 'S%' or ename like 's%';
select ename from emp where upper(ename) like 'S%';

select ename from emp where ename like '_A%' or ename like '_a%';
select ename from emp where ename like '_A' or ename like '_a';
-- 뒤의 %는 웬만하면 들어가는 게 좋다.

select * from emp where deptno = 20 and job in ('CLERK', 'ANALYST');
select * from emp where deptno = 20 and (job = 'CLERK' or job = 'ANALYST');
select * from emp where deptno = 20 and job = 'CLERK' or deptno = 20 and job = 'ANALYST';
select * from emp where not (deptno <> 20 or (job <> 'CLERK' and job <> 'ANALYST'));
select * from emp where not (deptno <> 20 or job <> 'CLERK' and job <> 'ANALYST');


select * from emp order by deptno asc, sal desc;
select * from emp where deptno in (10, 20) order by deptno asc, sal desc ;
--select * from emp order by deptno asc, sal desc where deptno in (10, 20) ;  -- 구문 순서로 인하여 오류 발생

select * from emp where deptno in (10, 20) and ename like '%A%' order by deptno asc, sal desc ;
select * from emp where deptno in (20, 30) and (ename like '%A%' or ename like '%a%' )order by deptno asc, sal desc ;

select ename, sal*12+coalesce(comm,0)as income 
    from emp 
    where sal*12+coalesce(comm,0) >= 36000 
    order by income;
select ename, sal*12+coalesce(comm,0)as income 
    from emp 
    where income >= 36000 
    order by income; -- wheredp select 구문의 alias가 쓰여서 오류
select *, sal*12+coalesce(comm,0)as income 
    from emp 
    where sal*12+coalesce(comm,0) >= 36000 
    order by income;-- 오라클은 *에 테이블을 달아줘야 함.
select emp.*, sal*12+coalesce(comm,0)as income 
    from emp 
    where sal*12+coalesce(comm,0) >= 36000 
    order by income;
select e.*, sal*12+coalesce(comm,0)as income 
    from emp e
    where sal*12+coalesce(comm,0) >= 36000 
    order by income; 
select * 
    from ( select emp.*, sal*12+coalesce(comm,0)as income 
                from emp )
    where income >= 36000 
    order by income;
select a.*, b.income 
    from( select empno, sal*12+coalesce(comm,0)as income
            from emp ) b 
    join emp a on a.empno = b.empno
    where income >= 36000
    order by income desc;

