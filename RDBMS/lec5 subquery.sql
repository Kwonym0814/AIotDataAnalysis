
select ename, sal 
    from emp
    where sal > (select sal from emp where ename = 'JONES');
    
select e.deptno, d.dname, e.ename, e.sal
    from emp e
    join (select deptno, avg(sal) as avg_sal from emp group by deptno)a
        on e.deptno = a.deptno and e.sal > a.avg_sal
    join dept d on e.deptno = d.deptno
    order by sal desc;
    
select min(sal) from emp group by deptno;

select empno, ename, job, sal 
    from emp
    where job in (select job from emp where empno = 7876)
        and sal > (select sal from emp where empno = 7369)
    ;
select empno, ename, sal
    from emp
    where sal > (select min(sal) from emp);

select empno, ename, sal
    from emp
    where sal > any (select sal from emp);
    
select empno, ename, sal
    from emp
    where sal > any (select sal from emp);
    
select e.deptno, d.dname, e.ename, e.sal
    from emp e
    join (select deptno, avg(sal) as avg_sal from emp group by deptno)a
        on e.deptno = a.deptno and e.sal > a.avg_sal
    join dept d on e.deptno = d.deptno
    order by sal desc;
 
select e.ename, e.sal
    from emp e
    where (e.deptno, sal) > any (select deptno, min(sal) from emp group by deptno);

with min_tbl as (
    select deptno, min(sal) as min_sal
        from emp
        group by deptno
)
select e.deptno, e.ename, e.sal
    from emp e 
    join min_tbl a on e.deptno = a.deptno
        and  e.sal > a.min_sal
    order by a.deptno asc, sal desc
    ;
    
select e.deptno, e.ename, e.sal
    from emp e
    join (select deptno, min(sal) as min_sal from emp group by deptno)a
        on e.deptno = a.deptno and e.sal > a.min_sal
    order by deptno asc, sal desc;
    
    
select e.deptno, e.sal, e.ename
    from emp e
    where sal > (
                    select min(sal)
                        from emp a
                        where a.deptno = e.deptno
                        group by a.deptno)
    order by e.deptno;
                        
    )


select e.ename, e.job, e.deptno
    from emp e 
    join (select job from emp where empno = 7521)a on e.job = a.job
    join (select deptno from emp where empno = 7654)b on e.deptno = b.deptno
    ;

select e.ename, e.job, e.deptno
    from emp e 
    where e.job in ( select job from emp where empno = 7521) 
    and e.deptno in (select deptno from emp where empno = 7654)
    ;
    

select e.ename, e.job, e.deptno
    from emp e 
    where e.job in ( select job from emp where empno = 7521) 
    and e.deptno in (select deptno from emp where empno = 7521)
    ;
    
select e.ename, e.job, e.deptno
    from emp e 
    where (e.job, e.deptno) in ( select job, deptno from emp where empno = 7521) 
    ;
    
select ename, job, deptno
from emp
where (job, deptno, sal) = (select job, deptno, sal from emp where empno=7521);

select count(1) from emp where deptno = 10;
select count(1) from emp where deptno = 20;


select deptno, min(sal) from emp
where min(sal) > 500
group by deptno;



select deptno, count(1)
from emp
group by deptno
having count(1) = (select max(count(1)) from emp group by deptno);