from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def pesos_a_centavos(monto: str) -> int:
    """Convierte monto recibido desde la interfaz al formato adecuado para la base dee datos.

    Args:
        monto (str): El monto a recibir.

    Raises:
        ValueError: El valor de MONTO no puede estar vacio
        ValueError: El valor de MONTO debe ser operable
        ValueError: El valor de MONTO debe ser finito
        ValueError: El valor de MONTO no debe ser negativo

    Returns:
        int: Valor de MONTO en CENTAVOS ENTEROS
    """
    monto_clean = monto.strip().replace(",", ".")
    if not monto_clean:
        raise ValueError("El monto no puede estar vacio.")

    try:
        valor = Decimal(monto_clean)
    except InvalidOperation:
        raise ValueError(f"'{monto}' no es un monto numerico valido")

    if not valor.is_finite():
        raise ValueError("El monto debe ser un numero valido")
    if valor < 0:
        raise ValueError("El monto no puede ser negativo")

    centavos = (valor * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(centavos)


def centavos_a_pesos(centavos: int, incluir_simbolo: bool = True) -> str:
    """Transforma los centavos ENTEROS enviados desde la BD en un formato STRING apropiado para la interfaz.

    Args:
        centavos (int): los centavos en INT
        incluir_simbolo (bool, optional): Inclusion del simbolo de dinero dentro del return. Defaults to True.

    Raises:
        ValueError: Centavos debe un ENTERO

    Returns:
        str: Cantidad converttida en pesos, con decimales y separaciones.
    """    
    if not isinstance(centavos, int):
        raise ValueError("El valor de centavos debe ser un numero entero.")

    pesos = Decimal(centavos) / Decimal("100")
    if incluir_simbolo:
        return f"$ {pesos:,.2f}"
    return f"{pesos:.2f}"
