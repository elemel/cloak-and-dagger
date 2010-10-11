from Box2D import *
import math
import pyglet
from pyglet.gl import *
import sys

def trace(line):
    sys.stderr.write('TRACE: %s\n' % line)

def debug(line):
    sys.stderr.write('DEBUG: %s\n' % line)

def info(line):
    sys.stderr.write('INFO: %s\n' % line)

def warn(line):
    sys.stderr.write('WARN: %s\n' % line)

def error(line):
    sys.stderr.write('ERROR: %s\n' % line)

def fatal(line):
    sys.stderr.write('FATAL: %s\n' % line)

def sign(x):
    if x < 0:
        return -1
    elif x > 0:
        return 1
    else:
        return 0

class Actor(object):
    def __init__(self, game_engine, stepping=False, drawing=False):
        self._game_engine = game_engine
        self.game_engine.add_actor(self)
        self._stepping = False
        self._drawing = False
        self.stepping = stepping
        self.drawing = drawing

    def delete(self):
        self.drawing = False
        self.stepping = False
        self.game_engine.remove_actor(self)
        self._game_engine = None

    @property
    def game_engine(self):
        return self._game_engine

    @property
    def stepping(self):
        return self._stepping

    @stepping.setter
    def stepping(self, stepping):
        stepping = bool(stepping)
        if stepping != self.stepping:
            self._stepping = stepping
            if self.stepping:
                self.game_engine.add_step_actor(self)
            else:
                self.game_engine.remove_step_actor(self)

    @property
    def drawing(self):
        return self._drawing

    @drawing.setter
    def drawing(self, drawing):
        drawing = bool(drawing)
        if drawing != self.drawing:
            self._drawing = drawing
            if self.drawing:
                self.game_engine.add_draw_actor(self)
            else:
                self.game_engine.remove_draw_actor(self)

    def begin_step(self, dt):
        pass

    def end_step(self, dt):
        pass

    def begin_contact(self, contact):
        pass

    def end_contact(self, contact):
        pass

    def draw(self):
        pass

class TabInLevelError(Exception):
    pass

class LevelParser(object):
    def __init__(self, level_file):
        self.level_file = level_file

    def parse(self):
        tiles = {}
        for y, line in enumerate(self.level_file):
            line = line.rstrip()
            if '\t' in line:
                raise TabInLevelError()
            for x, char in enumerate(line):
                if not char.isspace():
                    tiles[x, -y] = char
        return tiles

TILE_COLORS = dict(
    _=(0.0, 0.0, 0.0),
    a=(0.0, 0.0, 0.5),
    b=(0.0, 0.0, 1.0),
    c=(0.0, 0.5, 0.0),
    d=(0.0, 0.5, 0.5),
    e=(0.0, 0.5, 1.0),
    f=(0.0, 1.0, 0.0),
    g=(0.0, 1.0, 0.5),
    h=(0.0, 1.0, 1.0),
    i=(0.5, 0.0, 0.0),
    j=(0.5, 0.0, 0.5),
    k=(0.5, 0.0, 1.0),
    l=(0.5, 0.5, 0.0),
    m=(0.5, 0.5, 0.5),
    n=(0.5, 0.5, 1.0),
    o=(0.5, 1.0, 0.0),
    p=(0.5, 1.0, 0.5),
    q=(0.5, 1.0, 1.0),
    r=(1.0, 0.0, 0.0),
    s=(1.0, 0.0, 0.5),
    t=(1.0, 0.0, 1.0),
    u=(1.0, 0.5, 0.0),
    v=(1.0, 0.5, 0.5),
    w=(1.0, 0.5, 1.0),
    x=(1.0, 1.0, 0.0),
    y=(1.0, 1.0, 0.5),
    z=(1.0, 1.0, 1.0),
)

class LevelActor(Actor):
    def __init__(self, game_engine):
        super(LevelActor, self).__init__(game_engine, stepping=True,
                                         drawing=True)
        self.half_tile_width = 0.5
        self.half_tile_height = 0.5
        self.start_position = 0.0, 0.0
        level_name = 'resources/levels/level.txt'
        with pyglet.resource.file(level_name) as level_file:
            level_parser = LevelParser(level_file)
            self.tiles = level_parser.parse()
        self.body = self.game_engine.world.CreateStaticBody(userData=(self, None))
        self._init_tiles()

    def _init_tiles(self):
        for tile_position, tile_char in self.tiles.iteritems():
            tile_x, tile_y = tile_position
            if tile_char == '@':
                self.start_position = self.get_tile_center(tile_x, tile_y)
            elif tile_char == '/':
                center_x, center_y = self.get_tile_center(tile_x, tile_y)
                min_x, min_y, max_x, max_y = self.get_tile_bounds(tile_x,
                                                                  tile_y)
                vertices_1 = ((min_x, min_y), (max_x, min_y),
                              (max_x, center_y), (min_x, center_y))
                vertices_2 = ((center_x, center_y), (max_x, center_y),
                              (max_x, max_y), (center_x, max_y))
                user_data = self, (tile_position, tile_char)
                self.body.CreatePolygonFixture(vertices=vertices_1,
                                               userData=user_data)
                self.body.CreatePolygonFixture(vertices=vertices_2,
                                               userData=user_data)
            elif tile_char == '\\':
                center_x, center_y = self.get_tile_center(tile_x, tile_y)
                min_x, min_y, max_x, max_y = self.get_tile_bounds(tile_x,
                                                                  tile_y)
                vertices_1 = ((min_x, min_y), (max_x, min_y),
                              (max_x, center_y), (min_x, center_y))
                vertices_2 = ((min_x, center_y), (center_x, center_y),
                              (center_x, max_y), (min_x, max_y))
                user_data = self, (tile_position, tile_char)
                self.body.CreatePolygonFixture(vertices=vertices_1,
                                               userData=user_data)
                self.body.CreatePolygonFixture(vertices=vertices_2,
                                               userData=user_data)
            elif tile_char == '_':
                center_x, center_y = self.get_tile_center(tile_x, tile_y)
                min_x, min_y, max_x, max_y = self.get_tile_bounds(tile_x,
                                                                  tile_y)
                vertices = ((min_x, min_y), (max_x, min_y),
                            (max_x, center_y), (min_x, center_y))
                user_data = self, (tile_position, tile_char)
                self.body.CreatePolygonFixture(vertices=vertices,
                                               userData=user_data)
            elif tile_char == '^':
                center_x, center_y = self.get_tile_center(tile_x, tile_y)
                min_x, min_y, max_x, max_y = self.get_tile_bounds(tile_x,
                                                                  tile_y)
                vertices = ((min_x, center_y), (max_x, center_y),
                            (max_x, max_y), (min_x, max_y))
                user_data = self, (tile_position, tile_char)
                self.body.CreatePolygonFixture(vertices=vertices,
                                               userData=user_data)
            elif tile_char == '=':
                min_x, min_y, max_x, max_y = self.get_tile_bounds(tile_x,
                                                                  tile_y)
                vertices = ((min_x, min_y), (max_x, min_y),
                            (max_x, max_y), (min_x, max_y))
                user_data = self, (tile_position, tile_char)
                self.body.CreatePolygonFixture(vertices=vertices,
                                               userData=user_data)
            else:
                min_x, min_y, max_x, max_y = self.get_tile_bounds(tile_x,
                                                                  tile_y)
                vertices = ((min_x, min_y), (max_x, min_y),
                            (max_x, max_y), (min_x, max_y))
                user_data = self, (tile_position, tile_char)
                self.body.CreatePolygonFixture(vertices=vertices,
                                               userData=user_data)

    def get_tile_center(self, tile_x, tile_y):
        center_x = 2.0 * tile_x * self.half_tile_width
        center_y = 2.0 * tile_y * self.half_tile_height
        return center_x, center_y

    def get_tile_bounds(self, tile_x, tile_y):
        center_x, center_y = self.get_tile_center(tile_x, tile_y)
        min_x = center_x - self.half_tile_width
        min_y = center_y - self.half_tile_height
        max_x = center_x + self.half_tile_width
        max_y = center_y + self.half_tile_height
        return min_x, min_y, max_x, max_y

class Controls(object):
    def on_activate(self):
        pass

    def on_deactivate(self):
        pass

    def on_key_press(self, key, modifiers):
        pass

    def on_key_release(self, key, modifiers):
        pass

class ClosestRayCastCallback(b2RayCastCallback):
    def __init__(self, filter=None):
        super(ClosestRayCastCallback, self).__init__()
        self.filter = filter
        self.fixture = None
        self.point = None
        self.normal = None
        self.fraction = None

    def ReportFixture(self, fixture, point, normal, fraction):
        if ((self.fraction is None or fraction < self.fraction) and
            (self.filter is None or self.filter(fixture))):
            self.fixture = fixture
            self.point = point
            self.normal = normal
            self.fraction = fraction
        return 1.0

class Enumeration(object):
    def __init__(self, names):
        self._names = tuple(names.split())
        self._values = tuple(xrange(len(self._names)))
        for name, value in zip(self._names, self._values):
            setattr(self, name, value)

    @property
    def names(self):
        return self._names

    @property
    def values(self):
        return self._values

class CharacterActor(Actor):
    states = Enumeration("""
        CLIMB
        CRAWL
        CROUCH
        DEAD
        DIVE
        HANG
        JUMP
        PUSH
        RUN
        SLIDE
        STAND
        SWIM
        WALK
    """)

    air_states = states.CLIMB, states.HANG, states.JUMP
    ground_states = (states.CRAWL, states.CROUCH, states.PUSH, states.RUN,
                     states.STAND, states.WALK)

    def __init__(self, game_engine, name='UNKNOWN', position=(0.0, 0.0),
                 color=(255, 255, 255)):
        super(CharacterActor, self).__init__(game_engine, stepping=True,
                                             drawing=True)
        self.name = name
        self.face = 1
        self.walk_acceleration = 10.0
        self.max_walk_velocity = 5.0
        self.drift_acceleration = 5.0
        self.max_drift_velocity = 2.0
        self.min_jump_velocity = 7.0
        self.max_jump_velocity = 9.0
        self.half_width = 0.3
        self.half_height = 0.8
        self.color = color
        self._state = self.states.STAND
        self.radius = max(self.half_width, self.half_height)
        self.body = game_engine.world.CreateDynamicBody(position=position,
                                                        userData=(self, None))
        self.body.CreateCircleFixture(radius=self.radius, density=1.0,
                                      isSensor=True, userData=(self, None))

        self.left = False
        self.right = False
        self.up = False
        self.down = False
        self.jump = False

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        if state != self._state:
            debug('Character %s changes state from %s to %s.' %
                  (self.name, self.states.names[self._state],
                   self.states.names[state]))
        self._state = state

    def begin_step(self, dt):
        self._step_face()
        self._step_jump()
        if self.state == self.states.STAND and self.right - self.left:
            self.state = self.states.WALK
        if self.state == self.states.WALK and not self.right - self.left:
            self.state = self.states.STAND

        if self.state == self.states.WALK:
            vx, vy = self.body.linearVelocity
            vx += self.face * dt * self.walk_acceleration
            vx = sign(vx) * min(abs(vx), self.max_walk_velocity)
            self.body.linearVelocity = vx, vy
        if self.state == self.states.STAND:
            vx, vy = self.body.linearVelocity
            sx = sign(vx)
            vx -= sx * dt * self.walk_acceleration
            if sign(vx) != sx:
                vx = 0.0
            self.body.linearVelocity = vx, vy
        if self.state == self.states.JUMP:
            if self.left or self.right:
                vx, vy = self.body.linearVelocity
                if sign(vx) == self.right - self.left:
                    vx2 = vx + (self.right - self.left) * dt * self.drift_acceleration
                    vx2 = sign(vx2) * min(abs(vx2), self.max_drift_velocity)
                    vx = sign(vx) * max(abs(vx), abs(vx2))
                else:
                    vx += (self.right - self.left) * dt * self.drift_acceleration
                self.body.linearVelocity = vx, vy

    def _step_face(self):
        if self.right - self.left:
            self.face = self.right - self.left

    def _step_jump(self):
        if self.jump and self.state in self.ground_states:
            self.state = self.states.JUMP
            vx, vy = self.body.linearVelocity
            ratio = abs(vx) / self.max_walk_velocity
            ratio = min(ratio, 1.0)
            ratio **= 2
            vy = (ratio * self.min_jump_velocity +
                  (1.0 - ratio) * self.max_jump_velocity)
            self.body.linearVelocity = vx, vy

    def end_step(self, dt):
        self._step_ground()

    def _step_ground(self):
        callback = ClosestRayCastCallback()
        x, y = self.body.position
        p1 = x, y
        length = self.radius + 0.75
        p2 = x, y - length
        self.game_engine.world.RayCast(callback, p1, p2)
        if callback.fixture is None:
            if self.state in self.ground_states:
                self.state = self.states.JUMP
        else:
            distance = callback.fraction * length
            vx, vy = self.body.linearVelocity
            sticky = False
            if (self.state in self.ground_states or
                self.state in self.air_states and vy < 0.0 and
                distance < self.radius):
                x3, y3 = callback.point
                self.body.position = x, y3 + self.radius
                self.body.linearVelocity = vx, 0.0
                if self.state in self.air_states:
                    self.state = self.states.STAND

    def draw(self):
        glColor3ub(*self.color)

        x, y = self.body.position
        if self.state == self.states.CROUCH:
            half_width = 0.4
            half_height = 0.4
        else:
            half_width = self.half_width
            half_height = self.half_height
        min_x = x - half_width
        min_y = y - half_height
        max_x = x + half_width
        max_y = y + half_height
        glBegin(GL_POLYGON)
        glVertex2f(min_x, min_y)
        glVertex2f(max_x, min_y)
        glVertex2f(max_x, max_y)
        glVertex2f(min_x, max_y)
        glEnd()

    def on_key_press(self, key, modifiers):
        if key == pyglet.window.key.LEFT:
            self.left = True
        if key == pyglet.window.key.RIGHT:
            self.right = True
        if key == pyglet.window.key.UP:
            self.up = True
        if key == pyglet.window.key.DOWN:
            self.down = True
        if key == pyglet.window.key.SPACE:
            self.jump = True

    def on_key_release(self, key, modifiers):
        if key == pyglet.window.key.LEFT:
            self.left = False
        if key == pyglet.window.key.RIGHT:
            self.right = False
        if key == pyglet.window.key.UP:
            self.up = False
        if key == pyglet.window.key.DOWN:
            self.down = False
        if key == pyglet.window.key.SPACE:
            self.jump = False

def generate_circle_vertices(center=(0.0, 0.0), radius=1.0, angle=0.0,
                             vertex_count=256):
    cx, cy = center
    for i in xrange(vertex_count):
        vertex_angle = angle + 2.0 * math.pi * float(i) / float(vertex_count)
        vx = cx + radius * math.cos(vertex_angle)
        vy = cy + radius * math.sin(vertex_angle)
        yield vx, vy

class MyContactListener(b2ContactListener):
    def BeginContact(self, contact):
        actor_a, key_a = contact.fixtureA.userData
        actor_b, key_b = contact.fixtureB.userData
        actor_a.begin_contact(contact)
        actor_b.begin_contact(contact)

    def EndContact(self, contact):
        actor_a, key_a = contact.fixtureA.userData
        actor_b, key_b = contact.fixtureB.userData
        actor_a.end_contact(contact)
        actor_b.end_contact(contact)

class GameEngine(object):
    def __init__(self, view_width, view_height):
        self._view_width = view_width
        self._view_height = view_height
        self._time = 0.0
        self._world = b2World(gravity=(0.0, -13.0))
        self._contact_listener = MyContactListener()
        self._world.contactListener = self._contact_listener
        self._actors = set()
        self._step_actors = set()
        self._draw_actors = set()
        self._camera_scale = float(view_height) / 20.0
        self._level_actor = LevelActor(self)
        position = self._level_actor.start_position
        self._player_actor = CharacterActor(self, name='THIEF',
                                            position=position)
        self._circle_vertices = list(generate_circle_vertices())

    @property
    def time(self):
        return self._time

    @property
    def world(self):
        return self._world

    def delete(self):
        for actor in list(self._actors):
            actor.delete()
        assert not self._draw_actors
        assert not self._step_actors
        assert not self._actors

    def add_actor(self, actor):
        self._actors.add(actor)

    def remove_actor(self, actor):
        self._actors.remove(actor)

    def add_step_actor(self, actor):
        self._step_actors.add(actor)

    def remove_step_actor(self, actor):
        self._step_actors.remove(actor)

    def add_draw_actor(self, actor):
        self._draw_actors.add(actor)

    def remove_draw_actor(self, actor):
        self._draw_actors.remove(actor)

    def step(self, dt):
        self._time += dt
        for actor in list(self._step_actors):
            actor.begin_step(dt)
        self._world.Step(dt, 10, 10)
        for actor in list(self._step_actors):
            actor.end_step(dt)

    def draw(self):
        glPushMatrix()
        glTranslatef(self._view_width // 2, self._view_height // 2, 0)
        glScalef(self._camera_scale, self._camera_scale, self._camera_scale)
        x, y = self._player_actor.body.position
        glTranslatef(-x, -y, 0.0)
        for actor in list(self._draw_actors):
            actor.draw()
        self._debug_draw()
        glPopMatrix()

    def _debug_draw(self):
        glColor3f(0.0, 1.0, 0.0)
        for body in self.world.bodies:
            glPushMatrix()
            x, y = body.position
            glTranslatef(x, y, 0.0)
            angle = body.angle * 180.0 / math.pi
            glRotatef(angle, 0.0, 0.0, 1.0)
            for fixture in body.fixtures:
                shape = fixture.shape
                if isinstance(shape, b2PolygonShape):
                    glBegin(GL_LINE_LOOP)
                    for vx, vy in shape.vertices:
                        glVertex2f(vx, vy)
                    glEnd()
                elif isinstance(shape, b2CircleShape):
                    cx, cy = shape.pos
                    radius = shape.radius
                    glBegin(GL_LINE_LOOP)
                    stride = len(self._circle_vertices) / 16
                    for vx, vy in self._circle_vertices[::stride]:
                        glVertex2f(cx + radius * vx, cy + radius * vy)
                    glEnd()
                    glBegin(GL_LINES)
                    glVertex2f(cx, cy)
                    glVertex2f(cx + radius, cy)
                    glEnd()
                else:
                    assert False
            glPopMatrix()

    def on_key_press(self, key, modifiers):
        self._player_actor.on_key_press(key, modifiers)

    def on_key_release(self, key, modifiers):
        self._player_actor.on_key_release(key, modifiers)

class MyWindow(pyglet.window.Window):
    def __init__(self, **kwargs):
        super(MyWindow, self).__init__(**kwargs)
        if self.fullscreen:
            self.set_exclusive_mouse()
            self.set_exclusive_keyboard()
        self._game_engine = GameEngine(self.width, self.height)
        self._time = 0.0
        self._dt = 1.0 / 60.0
        pyglet.clock.schedule_interval(self._step, 0.1 * self._dt)
        self._clock_display = pyglet.clock.ClockDisplay()

    def close(self):
        pyglet.clock.unschedule(self._step)
        super(MyWindow, self).close()

    def _step(self, dt):
        self._time += dt
        if self._game_engine.time + self._dt < self._time:
            self._game_engine.step(self._dt)
        if self._game_engine.time + self._dt < self._time:
            # Skip frames.
            self._time = self._game_engine.time

    def on_draw(self):
        self.clear()
        self._game_engine.draw()
        self._clock_display.draw()

    def on_key_press(self, key, modifiers):
        if key == pyglet.window.key.ESCAPE:
            self.close()
        else:
            self._game_engine.on_key_press(key, modifiers)

    def on_key_release(self, key, modifiers):
        if key == pyglet.window.key.ESCAPE:
            pass
        else:
            self._game_engine.on_key_release(key, modifiers)

def main():
    fullscreen = '--fullscreen' in sys.argv
    window = MyWindow(caption='Cloak & Dagger', fullscreen=fullscreen)
    pyglet.app.run()

if __name__ == '__main__':
    main()
