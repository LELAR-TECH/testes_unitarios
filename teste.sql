SELECT
    ID_PEDIDO,
    ID_PRODUCTO,
    sum(valor)
FROM TESTE
GROUP BY
    ID_PEDIDO,
    2