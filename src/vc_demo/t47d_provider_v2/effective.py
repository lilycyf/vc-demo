"""Import old descriptive metadata into explicit, faithful executable settings."""
import copy


def canonical(config):
    c = copy.deepcopy(config)
    if c.get('parent_config'):
        c['parent_config'] = canonical(c['parent_config'])
    if c.get('model') == 'tracsed' and c.get('optimizer') == 'author_Adam_0.001_MSE':
        c.update(optimizer='adam', learning_rate=.001, loss='mean_squared_error')
    return c
