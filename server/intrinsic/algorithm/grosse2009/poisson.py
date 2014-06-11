import numpy as np
import pyamg
import scipy.sparse


def get_gradients(I):
    """Get the vertical (derivative-row) and horizontal (derivative-column) gradients
    of an image."""
    I_y = np.zeros(I.shape)
    I_y[1:, :, ...] = I[1:, :, ...] - I[:-1, :, ...]
    I_x = np.zeros(I.shape)
    I_x[:, 1:, ...] = I[:, 1:, ...] - I[:, :-1, ...]
    return I_y, I_x

def solve(t_y, t_x, mask, t_y_weights=None, t_x_weights=None):
    """Solve for the image which best matches the target vertical gradients
    t_y and horizontal gradients t_x, e.g. the one which minimizes sum of squares
    of the residual

       sum of (I[i,j] - I[i-1,j] - t_y[i,j])**2 + (I[i,j] - I[i,j-1] - t_x[i,j])**2

    Only considers the target gradients lying entirely within the mask.
    The first row of t_y and the first column of t_x are ignored. Optionally,
    you may pass in an array with the weights corresponding to each target
    gradient. The solution is unique up to a constant added to each of
    the pixels. """
    if t_y_weights is None:
        t_y_weights = np.ones(t_y.shape)
    if t_x_weights is None:
        t_x_weights = np.ones(t_x.shape)
    M, N = mask.shape
    numbers = get_numbers(mask)
    A = get_A(mask, t_y_weights, t_x_weights)
    b = get_b(t_y, t_x, mask, t_y_weights, t_x_weights)

    solver = pyamg.ruge_stuben_solver(A)
    x = solver.solve(b)
    
    I = np.zeros(mask.shape)
    for i in range(M):
        for j in range(N):
            I[i,j] = x[numbers[i,j]]
    return I

def solve_L1(t_y, t_x, mask):
    """Same as solve(), except using an L1 penalty rather than least squares."""
    EPSILON = 0.0001

    # We minimize the L1-norm of the residual
    #
    #    sum of |r_i|
    #    r = Ax - b
    #
    # by alternately minimizing the variational upper bound
    #
    #    |r_i| <= a_i * r_i**2 + 1 / (4 * a_i)
    #
    # with respect to x and a. When r is fixed, this bound is tight for a = 1 / (2 * r).
    # When a is fixed, we optimize for x by solving a weighted least-squares problem.

    I = solve(t_y, t_x, mask)
    for i in range(20):
        I_y, I_x = get_gradients(I)
        t_y_err = mask * np.abs(I_y - t_y)
        t_x_err = mask * np.abs(I_x - t_x)

        t_y_weights = 1. / (2. * np.clip(t_y_err, EPSILON, np.infty))
        t_x_weights = 1. / (2. * np.clip(t_x_err, EPSILON, np.infty))

        try:
            I = solve(t_y, t_x, mask, t_y_weights, t_x_weights)
        except:
            # Occasionally the solver fails when the weights get very large
            # or small. In that case, we just return the previous iteration's
            # estimate, which is hopefully close enough.
            return I

    return I




###################### Stuff below here not very readable ##########################
        
def get_numbers(mask):
    M, N = mask.shape
    numbers = np.zeros(mask.shape, dtype=int)
    count = 0
    for i in range(M):
        for j in range(N):
            if mask[i,j]:
                numbers[i, j] = count
                count += 1

    return numbers

def get_b(t_y, t_x, mask, t_y_weights, t_x_weights):
    M, N = mask.shape
    t_y = t_y[1:, :]
    t_y_weights = t_y_weights[1:, :]
    t_x = t_x[:, 1:]
    t_x_weights = t_x_weights[:, 1:]
    numbers = get_numbers(mask)
    K = np.max(numbers) + 1
    b = np.zeros(K)
        

    # horizontal derivatives
    for i in range(M):
        for j in range(N-1):
            if mask[i,j] and mask[i,j+1]:
                n1 = numbers[i,j]
                n2 = numbers[i,j+1]

                # row (i,j): -x_{i,j+1} + x_{i,j} + t
                b[n1] -= t_x[i,j] * t_x_weights[i,j]

                # row (i, j+1): x_{i,j+1} - x_{i,j} - t
                b[n2] += t_x[i,j] * t_x_weights[i,j]


    # vertical derivatives
    for i in range(M-1):
        for j in range(N):
            if mask[i,j] and mask[i+1,j]:
                n1 = numbers[i,j]
                n2 = numbers[i+1,j]

                # row (i,j): -x_{i+1,j} + x_{i,j} + t
                b[n1] -= t_y[i,j] * t_y_weights[i,j]

                # row (i, j+1): x_{i+1,j} - x_{i,j} - t
                b[n2] += t_y[i,j] * t_y_weights[i,j]


    return b

def get_A(mask, t_y_weights, t_x_weights):
    M, N = mask.shape
    numbers = get_numbers(mask)
    K = np.max(numbers) + 1
    
    t_y_weights = t_y_weights[1:, :]
    t_x_weights = t_x_weights[:, 1:]

    # horizontal derivatives
    count = 0
    for i in range(M):
        for j in range(N-1):
            if mask[i,j] and mask[i,j+1]:
                count += 1
    data = np.zeros(4*count)
    row = np.zeros(4*count)
    col = np.zeros(4*count)
    count = 0
    for i in range(M):
        for j in range(N-1):
            if mask[i,j] and mask[i,j+1]:
                n1 = numbers[i,j]
                n2 = numbers[i,j+1]

                # row (i,j): -x_{i,j+1} + x_{i,j} + t
                row[4*count] = n1
                col[4*count] = n2
                data[4*count] = -t_x_weights[i, j]

                row[4*count+1] = n1
                col[4*count+1] = n1
                data[4*count+1] = t_x_weights[i, j]

                # row (i, j+1): x_{i,j+1} - x_{i,j} - t
                row[4*count+2] = n2
                col[4*count+2] = n2
                data[4*count+2] = t_x_weights[i, j]

                row[4*count+3] = n2
                col[4*count+3] = n1
                data[4*count+3] = -t_x_weights[i, j]

                count += 1

    data1 = data
    row1 = row
    col1 = col

    # vertical derivatives
    count = 0
    for i in range(M-1):
        for j in range(N):
            if mask[i,j] and mask[i+1,j]:
                count += 1
    data = np.zeros(4*count)
    row = np.zeros(4*count)
    col = np.zeros(4*count)
    count = 0
    for i in range(M-1):
        for j in range(N):
            if mask[i,j] and mask[i+1,j]:
                n1 = numbers[i,j]
                n2 = numbers[i+1,j]

                # row (i,j): -x_{i+1,j} + x_{i,j} + t
                row[4*count] = n1
                col[4*count] = n2
                data[4*count] = -t_y_weights[i, j]

                row[4*count+1] = n1
                col[4*count+1] = n1
                data[4*count+1] = t_y_weights[i, j]

                # row (i, j+1): x_{i+1,j} - x_{i,j} - t
                row[4*count+2] = n2
                col[4*count+2] = n2
                data[4*count+2] = t_y_weights[i, j]

                row[4*count+3] = n2
                col[4*count+3] = n1
                data[4*count+3] = -t_y_weights[i, j]

                count += 1

    data2 = data
    row2 = row
    col2 = col

    data = np.concatenate([data1, data2])
    row = np.concatenate([row1, row2])
    col = np.concatenate([col1, col2])

    return scipy.sparse.coo_matrix((data, (row, col)), shape=(K, K))
