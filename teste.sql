SELECT
    ID_PEDIDO,
    ID_PRODUCTO,
    sum(valor)
FROM TESTE
GROUP BY
    1,
    2