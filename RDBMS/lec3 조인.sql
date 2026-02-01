--¡∂¿Œ(JOIN)

select *
    from emp, dept;
select *
    from emp, dept
    order by ename asc, dept.deptno asc;
select *
    from emp, dept
    order by ename asc, dept.deptno asc;    
    
    
CREATE TABLE SALGRADE
      ( GRADE NUMBER,
	LOSAL NUMBER,
	HISAL NUMBER );
INSERT INTO SALGRADE VALUES (1,700,1200);
INSERT INTO SALGRADE VALUES (2,1201,1400);
INSERT INTO SALGRADE VALUES (3,1401,2000);
INSERT INTO SALGRADE VALUES (4,2001,3000);
INSERT INTO SALGRADE VALUES (5,3001,9999);

select * from salgrade;

COMMIT;

select e.ename, s.grade
    from emp e, salgrade s
    where e.sal between s.losal and s.hisal;
    
select e.ename, s.grade
    from emp e join salgrade s
    on e.sal between s.losal and s.hisal;
    

select c.com_seq, c.com_name, g.good_seq, g.good_name, g.good_price
    from COMPANY_GOODS cg
    left join company c on cg.com_seq = c.com_seq
    left join goods g on cg.good_seq = g.good_seq
    where cg.com_SEQ = 1;

select o.order_code, o.user_seq, o.tot_price, o.order_date, og.good_seq, og.good_price, og.order_amount, og.order_price, g.good_name
    from ORDERS_GOODS og
    left join ORDERS o on og.order_code = o.order_code
    left join goods g on og.good_seq = g.good_seq
    where o.order_code = 'n00001';
    
select u.user_seq, u.user_id, u.user_name, u.user_pw, u.user_mobile, u.user_gubun, coalesce(f.ASAL+p.TSAL, f.ASAL, p.TsAL) as sal
    from users u
    left join parttime p on u.user_seq = p.user_seq
    left join fulltime f on u.user_seq = f.user_seq;
    
 select u.user_seq, u.user_id, u.user_name, u.mgr_seq, m.user_id as mgr_id, m.user_name as mgr_name
    from users u
    left join ( select user_seq, user_id, user_name 
                    from users) m on u.mgr_seq = m.user_seq
    order by u.user_seq;
    
    