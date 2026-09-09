"""ingredientes, extras, tamanos y estados cerrados

Revision ID: b566cf8751a6
Revises: bf577fff3248
Create Date: 2026-09-09 16:38:12.062618

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b566cf8751a6'
down_revision = 'bf577fff3248'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'product_sizes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('size', sa.String(length=20), nullable=False),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.CheckConstraint("size IN ('chica', 'mediana', 'grande', 'unica')", name='ck_product_sizes_size'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='fk_product_sizes_product_id_products'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id', 'size', name='uq_product_sizes_product_id_size'),
    )
    op.create_index('ix_product_sizes_product_id', 'product_sizes', ['product_id'])

    op.create_table(
        'product_ingredients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_size_id', sa.Integer(), nullable=False),
        sa.Column('inventory_item_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.ForeignKeyConstraint(
            ['inventory_item_id'], ['inventory_items.id'],
            name='fk_product_ingredients_inventory_item_id_inventory_items',
        ),
        sa.ForeignKeyConstraint(
            ['product_size_id'], ['product_sizes.id'],
            name='fk_product_ingredients_product_size_id_product_sizes',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_size_id', 'inventory_item_id', name='uq_product_ingredients_size_item'),
    )
    op.create_index('ix_product_ingredients_inventory_item_id', 'product_ingredients', ['inventory_item_id'])
    op.create_index('ix_product_ingredients_product_size_id', 'product_ingredients', ['product_size_id'])

    op.create_table(
        'order_item_extras',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_item_id', sa.Integer(), nullable=False),
        sa.Column('inventory_item_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=10), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=2), server_default=sa.text('1'), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.CheckConstraint("action IN ('add', 'remove')", name='ck_order_item_extras_action'),
        sa.ForeignKeyConstraint(
            ['inventory_item_id'], ['inventory_items.id'],
            name='fk_order_item_extras_inventory_item_id_inventory_items',
        ),
        sa.ForeignKeyConstraint(
            ['order_item_id'], ['order_items.id'],
            name='fk_order_item_extras_order_item_id_order_items',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_order_item_extras_inventory_item_id', 'order_item_extras', ['inventory_item_id'])
    op.create_index('ix_order_item_extras_order_item_id', 'order_item_extras', ['order_item_id'])

    with op.batch_alter_table('inventory_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_offerable_extra', sa.Boolean(), server_default=sa.text('false'), nullable=False))
        batch_op.add_column(sa.Column('extra_price', sa.Numeric(precision=10, scale=2), nullable=True))

    # --- Datos: price_small/medium/large (columnas viejas, aun presentes aqui) -> filas de product_sizes ---
    products_t = sa.table(
        'products',
        sa.column('id', sa.Integer),
        sa.column('price_small', sa.Numeric),
        sa.column('price_medium', sa.Numeric),
        sa.column('price_large', sa.Numeric),
    )
    product_sizes_t = sa.table(
        'product_sizes',
        sa.column('id', sa.Integer),
        sa.column('product_id', sa.Integer),
        sa.column('size', sa.String),
        sa.column('price', sa.Numeric),
    )
    bind = op.get_bind()
    for pid, small, medium, large in bind.execute(
        sa.select(products_t.c.id, products_t.c.price_small, products_t.c.price_medium, products_t.c.price_large)
    ).fetchall():
        for size_name, price in (('chica', small), ('mediana', medium), ('grande', large)):
            if price is not None:
                bind.execute(product_sizes_t.insert().values(product_id=pid, size=size_name, price=price))
        if small is None and medium is None and large is None:
            # Producto legado sin ningun precio: placeholder en 0 para no dejar order_items sin tamano.
            bind.execute(product_sizes_t.insert().values(product_id=pid, size='unica', price=0))

    with op.batch_alter_table('order_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('product_size_id', sa.Integer(), nullable=True))

    # --- Datos: order_items.size (texto libre) -> order_items.product_size_id ---
    order_items_t = sa.table(
        'order_items',
        sa.column('id', sa.Integer),
        sa.column('product_id', sa.Integer),
        sa.column('size', sa.String),
        sa.column('product_size_id', sa.Integer),
    )
    for item_id, pid, legacy_size in bind.execute(
        sa.select(order_items_t.c.id, order_items_t.c.product_id, order_items_t.c.size)
    ).fetchall():
        normalized = (legacy_size or '').strip().lower()
        match = bind.execute(
            sa.select(product_sizes_t.c.id).where(
                product_sizes_t.c.product_id == pid,
                sa.func.lower(product_sizes_t.c.size) == normalized,
            )
        ).first()
        if match is None:
            # Sin match exacto (texto legado con mayusculas/typo, o producto de un solo tamano): usa el unico disponible.
            match = bind.execute(
                sa.select(product_sizes_t.c.id).where(product_sizes_t.c.product_id == pid)
            ).first()
        if match is not None:
            bind.execute(
                order_items_t.update().where(order_items_t.c.id == item_id).values(product_size_id=match[0])
            )

    with op.batch_alter_table('order_items', schema=None) as batch_op:
        batch_op.alter_column('product_size_id', existing_type=sa.Integer(), nullable=False)
        batch_op.create_index('ix_order_items_order_id', ['order_id'], unique=False)
        batch_op.create_foreign_key(
            'fk_order_items_product_size_id_product_sizes', 'product_sizes', ['product_size_id'], ['id']
        )
        batch_op.drop_column('size')

    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_by_user_id', sa.Integer(), nullable=True))
        batch_op.create_index('ix_orders_created_by_user_id', ['created_by_user_id'], unique=False)
        batch_op.create_index('ix_orders_status', ['status'], unique=False)
        batch_op.create_foreign_key('fk_orders_created_by_user_id_users', 'users', ['created_by_user_id'], ['id'])
        # Alembic no autodetecta altas de CHECK sobre tablas ya existentes; se agrega a mano.
        batch_op.create_check_constraint(
            'ck_orders_status', "status IN ('taken', 'kitchen', 'ready', 'delivered', 'paid')"
        )

    with op.batch_alter_table('tables', schema=None) as batch_op:
        batch_op.create_check_constraint('ck_tables_status', "status IN ('free', 'occupied', 'closing')")

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.create_index('ix_products_category', ['category'], unique=False)
        batch_op.drop_column('price_medium')
        batch_op.drop_column('price_large')
        batch_op.drop_column('price_small')


def downgrade():
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('price_small', sa.NUMERIC(precision=10, scale=2), nullable=True))
        batch_op.add_column(sa.Column('price_medium', sa.NUMERIC(precision=10, scale=2), nullable=True))
        batch_op.add_column(sa.Column('price_large', sa.NUMERIC(precision=10, scale=2), nullable=True))
        batch_op.drop_index('ix_products_category')

    # --- Datos: product_sizes -> price_small/medium/large (best effort; 'unica' se vuelca a price_medium) ---
    products_t = sa.table(
        'products',
        sa.column('id', sa.Integer),
        sa.column('price_small', sa.Numeric),
        sa.column('price_medium', sa.Numeric),
        sa.column('price_large', sa.Numeric),
    )
    product_sizes_t = sa.table(
        'product_sizes',
        sa.column('id', sa.Integer),
        sa.column('product_id', sa.Integer),
        sa.column('size', sa.String),
        sa.column('price', sa.Numeric),
    )
    bind = op.get_bind()
    for size_name in ('chica', 'mediana', 'grande'):
        column_name = {'chica': 'price_small', 'mediana': 'price_medium', 'grande': 'price_large'}[size_name]
        for pid, price in bind.execute(
            sa.select(product_sizes_t.c.product_id, product_sizes_t.c.price).where(product_sizes_t.c.size == size_name)
        ).fetchall():
            bind.execute(products_t.update().where(products_t.c.id == pid).values(**{column_name: price}))
    # 'unica' (ej. bebidas) no tiene columna propia: cae en price_medium si sigue vacia.
    for pid, price in bind.execute(
        sa.select(product_sizes_t.c.product_id, product_sizes_t.c.price).where(product_sizes_t.c.size == 'unica')
    ).fetchall():
        bind.execute(
            products_t.update()
            .where(products_t.c.id == pid, products_t.c.price_medium.is_(None))
            .values(price_medium=price)
        )

    with op.batch_alter_table('tables', schema=None) as batch_op:
        batch_op.drop_constraint('ck_tables_status', type_='check')

    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_constraint('ck_orders_status', type_='check')
        batch_op.drop_constraint('fk_orders_created_by_user_id_users', type_='foreignkey')
        batch_op.drop_index('ix_orders_status')
        batch_op.drop_index('ix_orders_created_by_user_id')
        batch_op.drop_column('created_by_user_id')

    with op.batch_alter_table('order_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('size', sa.VARCHAR(length=20), nullable=True))

    # --- Datos: product_sizes.size (via product_size_id) -> order_items.size ---
    order_items_t = sa.table(
        'order_items',
        sa.column('id', sa.Integer),
        sa.column('size', sa.String),
        sa.column('product_size_id', sa.Integer),
    )
    for item_id, size_name in bind.execute(
        sa.select(order_items_t.c.id, product_sizes_t.c.size).select_from(
            order_items_t.join(product_sizes_t, order_items_t.c.product_size_id == product_sizes_t.c.id)
        )
    ).fetchall():
        bind.execute(order_items_t.update().where(order_items_t.c.id == item_id).values(size=size_name))

    with op.batch_alter_table('order_items', schema=None) as batch_op:
        batch_op.alter_column('size', existing_type=sa.VARCHAR(length=20), nullable=False)
        batch_op.drop_constraint('fk_order_items_product_size_id_product_sizes', type_='foreignkey')
        batch_op.drop_index('ix_order_items_order_id')
        batch_op.drop_column('product_size_id')

    with op.batch_alter_table('inventory_items', schema=None) as batch_op:
        batch_op.drop_column('extra_price')
        batch_op.drop_column('is_offerable_extra')

    op.drop_table('order_item_extras')
    op.drop_table('product_ingredients')
    op.drop_table('product_sizes')
