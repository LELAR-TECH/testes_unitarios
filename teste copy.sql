SELECT
    ID_PEDIDO,
    ID_PRODUCTO,
    sum(valor) as valor
FROM TESTE
GROUP BY
    1,
    ID_PRODUCTO


    