create table tmp1 (
a VARCHAR2(10),
b VARCHAR2(10));

create table tmp2 (
a VARCHAR2(10),
d VARCHAR2(10));

insert into tmp1 values ('a1', 'b1');
insert into tmp1 values ('a2', 'b2');
insert into tmp1 values ('a3', 'b3');
insert into tmp1 values ('a4', 'b4');

insert into tmp2 values ('a2', 'd2');
insert into tmp2 values ('a3', 'd3');
insert into tmp2 values ('a4', 'd4');
insert into tmp2 values ('a5', 'd5');

select * from tmp1;
select * from tmp2;

select b.b, b.a as a1, d.a as a2, d.d
    from tmp1 b 
    inner join tmp2 d on b.a = d.a;
    
select b.b, b.a as a1, d.a as a2, d.d
    from tmp1 b 
    left join tmp2 d on b.a = d.a;
    
select b.b, b.a as a1, d.a as a2, d.d
    from tmp1 b 
    right join tmp2 d on b.a = d.a;
    
select b.b, b.a as a1, d.a as a2, d.d
    from tmp1 b 
    full join tmp2 d on b.a = d.a;
    
    
