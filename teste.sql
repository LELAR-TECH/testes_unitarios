SELECT
    ID_PEDIDO,
    ID_PRODUCTO,
    sum(valor) as valor
FROM TESTE
GROUP BY
    ID_PEDIDO,
    ID_PRODUCTO
    
    