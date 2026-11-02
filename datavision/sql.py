import duckdb
import sqlglot
from sqlglot import exp

# Deliberately small SQL subset: no table functions, CTEs, subqueries or arbitrary functions.
ALLOWED = {"Select", "From", "Column", "Identifier", "Table", "Star", "Alias", "Literal", "Where", "Group", "Order", "Ordered", "Limit", "Offset", "And", "Or", "Not", "EQ", "NEQ", "GT", "GTE", "LT", "LTE", "Add", "Sub", "Mul", "Div", "Mod", "Paren", "Neg", "Is", "Null", "Boolean", "Count", "Sum", "Avg", "Min", "Max", "Distinct", "Having", "Like", "ILike", "In", "Between"}

def query(df, sql, limit=1000):
    try:
        statements = sqlglot.parse(sql, read="duckdb")
        if len(statements) != 1 or not isinstance(statements[0], exp.Select): raise ValueError("Solo se admite una consulta SELECT.")
        tree = statements[0]
        for node in tree.walk():
            if type(node).__name__ not in ALLOWED: raise ValueError(f"Construcción SQL no permitida: {type(node).__name__}.")
            if isinstance(node, exp.Table) and (node.name.lower() != "datos" or node.db or node.catalog): raise ValueError("Solo se puede consultar la tabla datos.")
        con = duckdb.connect(config={"enable_external_access": "false", "allow_unsigned_extensions": "false", "autoload_known_extensions": "false", "autoinstall_known_extensions": "false"})
        try:
            con.register("datos", df)
            return con.execute(f"SELECT * FROM ({tree.sql(dialect='duckdb')}) AS resultado LIMIT {int(limit)}").df()
        finally: con.close()
    except Exception as exc:
        raise ValueError(f"Consulta no válida o no permitida: {exc}") from exc

