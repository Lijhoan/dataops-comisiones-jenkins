/*
** Conexion a Base de datos clase
Tipo		: Postgresql
Host		: HOST_DE_BD
Puerto		: 5432
Database	: dmc
Schema		: rrhh

Usuario		: USUARIO_BD
Contraseña	: PASSWORD_BD

*/

SELECT cod_departamento, des_departamento
FROM rrhh.Departamento;


SELECT empleado_id, tip_documento, num_documento, nom_empleado, ape_empleado, cod_cargo, cod_departamento, mnt_salario, mnt_tope_comision
FROM rrhh.Empleado;


SELECT cod_cargo, des_cargo
FROM rrhh.cargo;