import generic as g


class NearestTest(g.unittest.TestCase):

    def test_naive(self):
        '''
        Test the naive nearest point function
        '''

        # generate a unit sphere mesh
        sphere = g.trimesh.primitives.Sphere(subdivisions=4)

        # randomly sample surface of a unit sphere, then expand to radius 2.0
        points = g.trimesh.sample.sample_surface_sphere(100) * 2

        # use the triangles from the unit sphere
        triangles = sphere.triangles

        # do the check
        closest, distance, tid = g.trimesh.proximity.closest_point_naive(sphere,
                                                                         points)

        # the distance from a sphere of radius 1.0 to a sphere of radius 2.0
        # should be pretty darn close to 1.0
        self.assertTrue((g.np.abs(distance - 1.0) < .01).all())

        # the vector for the closest point should be the same as the vector
        # to the query point
        vector = g.trimesh.util.diagonal_dot(closest, points / 2.0)
        self.assertTrue((g.np.abs(vector - 1.0) < .01).all())

    def test_helper(self):
        # just make sure the plumbing returns something
        for mesh in g.get_meshes(2):
            points = (g.np.random.random((100, 3)) - .5) * 100

            a = mesh.nearest.on_surface(points)
            self.assertTrue(a is not None)

            b = mesh.nearest.vertex(points)
            self.assertTrue(b is not None)

    def test_nearest_naive(self):
        funs = [g.trimesh.proximity.closest_point_naive,
                g.trimesh.proximity.closest_point]

        data_points = g.deque()
        data_dist = g.deque()

        tic = [g.time.time()]
        for i in funs:
            p, d = self.check_nearest_point_function(i)
            data_points.append(p)
            data_dist.append(d)
            tic.append(g.time.time())

        self.assertTrue(g.np.ptp(data_points, axis=0).max() < g.tol.merge)
        self.assertTrue(g.np.ptp(data_dist, axis=0).max() < g.tol.merge)

        log_msg = '\n'.join("{}: {}s".format(i, j) for i, j in zip([i.__name__ for i in funs],
                                                                   g.np.diff(tic)))
        g.log.info(
            'Compared the following nearest point functions:\n' +
            log_msg)

    def check_nearest_point_function(self, fun):
        def plot_tri(tri, color='g'):
            plottable = g.np.vstack((tri, tri[0]))
            plt.plot(plottable[:, 0], plottable[:, 1], color=color)

        def points_on_circle(count):
            theta = g.np.linspace(0, g.np.pi * 2, count + 1)[:count]
            s = g.np.column_stack((theta, [g.np.pi / 2] * count))
            t = g.trimesh.util.spherical_to_vector(s)
            return t

        # inscribed triangle on a circle on the XY plane
        triangle = points_on_circle(3)

        # a circle of points surrounding the triangle
        query = points_on_circle(63) * 2
        # set the points up in space
        query[:, 2] = 10
        # a circle of points inside the triangle
        query = g.np.vstack((query, query * .1))

        mesh = g.Trimesh(**g.trimesh.triangles.to_kwargs([triangle]))

        result, result_distance, result_tid = fun(mesh, query)

        polygon = g.Polygon(triangle[:, 0:2])
        polygon_buffer = polygon.buffer(1e-5)

        # all of the points returned should be on the triangle we're querying
        broken = g.np.array([not polygon_buffer.intersects(
            g.Point(i)) for i in result[:, 0:2]])

        # see what distance shapely thinks the nearest point is for the 2D triangle
        # and the query points
        distance_shapely = g.np.array(
            [polygon.distance(g.Point(i)) for i in query[:, 0:2]])

        # see what distance our function returned for the nearest point
        distance_ours = ((query[:, 0:2] - result[:, 0:2])
                         ** 2).sum(axis=1) ** .5

        # how far was our distance from the one shapely gave
        distance_test = g.np.abs(distance_shapely - distance_ours)

        assert not broken.any()
        assert distance_test.max() < g.trimesh.constants.tol.merge

        return result, result_distance

    def test_coplanar_signed_distance(self):
        mesh = g.trimesh.primitives.Box()

        # should be well outside the box but coplanar with a face
        # so the signed distance should be negative
        distance = mesh.nearest.signed_distance([mesh.bounds[0] + [100, 0, 0]])

        assert distance[0] < 0.0

        # constructed so origin is inside but also coplanar with
        # the nearest face
        mesh = g.get_mesh('origin_inside.STL')

        # origin should be inside, so distance should be positive
        distance = mesh.nearest.signed_distance([[0, 0, 0]])

        assert distance[0] > 0.0

    def test_edge_case(self):
        mesh = g.get_mesh('20mm-xyz-cube.stl')
        assert (mesh.nearest.signed_distance([[-51, 4.7, -20.6]]) < 0.0).all()


if __name__ == '__main__':
    g.trimesh.util.attach_to_log()
    g.unittest.main()
