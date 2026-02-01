
select max(sal), min(sal), round(avg(sal),2), sum(sal), count(ename)
    from emp;
    
select deptno, max(sal), min(sal), round(avg(sal),2), sum(sal), count(ename)
    from emp
    group by deptno
    order by deptno;
    
select max(e.sal), min(e.sal), round(avg(e.sal),2), sum(e.sal), count(e.ename)
    from emp e
    group by e.deptno
    having deptno > 10
    order by e.deptno;
    
select deptno, count(ename) as n_of_peaple, sum(sal)
    from emp
    group by deptno
    having count(ename) > 4
    order by deptno;

    
select deptno, count(ename) as n_of_peaple, sum(sal)
    from emp
    group by deptno
    order by count(ename) desc;
    
select deptno, count(ename) from emp group by deptno;
select max(n_of_people)
    from (select deptno, count(ename) as n_of_people from emp group by deptno)
    ;
    
select deptno, count(ename) as n_of_peaple, sum(sal)
    from emp 
    group by deptno
    having count(ename) in  ( select max(count(ename)) as n_of_people 
                                      from emp 
                                      group by deptno);

select deptno, round(avg(sal),2) as avg_sal
    from emp
    group by deptno
    order by deptno asc;
    
select round(12.50, 0) from dual;
select round(13.50, 0) from dual;
select round(12.5, 0) from dual;
select round(13.5, 0) from dual;
select ceil(146) from dual;

직업별 사원수, 최고급여 출력

select job, count(1), max(sal)
    from emp
    group by job;
    
select deptno, sum(sal)
    from emp
    group by deptno
    having sum(sal) >= 9000;
    
select deptno, job, trunc(avg(sal))
    from emp
    group by deptno, job
    order by deptno, job;

select deptno, substr(hiredate, 0,4) as hire_year, ceil(avg(sal))
    from emp
    group by deptno, substr(hiredate, 0,4)
    order by deptno, hire_year;
    
select deptno, extract(year from hiredate) as hire_year, ceil(avg(sal))
    from emp
    group by deptno, extract(year from hiredate)
    order by deptno, hire_year;

select deptno, to_char(hiredate,'YYYY') as hire_year, ceil(avg(sal))
    from emp
    group by deptno, to_char(hiredate,'YYYY')
    order by deptno, hire_year;    
    
select ceil(-13.4) from dual;