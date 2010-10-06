import pyglet
from pyglet.gl import *
from Box2D import *

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

    def step(self, dt):
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
        level_name = 'resources/levels/level.txt'
        with pyglet.resource.file(level_name) as level_file:
            level_parser = LevelParser(level_file)
            self.tiles = level_parser.parse()

    def draw(self):
        for tile_position, tile_char in self.tiles.iteritems():
            tile_x, tile_y = tile_position

            default_color = 1.0, 1.0, 1.0
            tile_color = TILE_COLORS.get(tile_char, default_color)
            glColor3f(*tile_color)

            min_x = float(tile_x) - self.half_tile_width
            min_y = float(tile_y) - self.half_tile_height
            max_x = float(tile_x) + self.half_tile_width
            max_y = float(tile_y) + self.half_tile_height
            glBegin(GL_POLYGON)
            glVertex2f(min_x, min_y)
            glVertex2f(max_x, min_y)
            glVertex2f(max_x, max_y)
            glVertex2f(min_x, max_y)
            glEnd()

class Controls(object):
    def on_activate(self):
        pass

    def on_deactivate(self):
        pass

    def on_key_press(self, key, modifiers):
        pass

    def on_key_release(self, key, modifiers):
        pass

class CharacterControls(Controls):
    def __init__(self, actor):
        self.actor = actor

    def on_key_press(self, key, modifiers):
        if key == pyglet.window.key.DOWN:
            self.actor.state = self.actor.CROUCH_STATE

    def on_key_release(self, key, modifiers):
        if key == pyglet.window.key.DOWN:
            self.actor.state = self.actor.STAND_STATE

class CharacterActor(Actor):
    (
        CLIMB_STATE,
        CRAWL_STATE,
        CROUCH_STATE,
        DEAD_STATE,
        FALL_STATE,
        FLOOR_SLIDE_STATE,
        HANG_STATE,
        HIDE_STATE,
        LIE_STATE,
        RUN_STATE,
        STAND_STATE,
        WALK_STATE,
        JUMP_STATE,
        PULL_STATE,
        PUSH_STATE,
        WALL_SLIDE_STATE,
    ) = xrange(16)

    def __init__(self, game_engine, x=0.0, y=0.0, color=(255, 255, 255)):
        super(CharacterActor, self).__init__(game_engine, stepping=True,
                                             drawing=True)
        self.x = x
        self.y = y
        self.half_width = 0.3
        self.half_height = 0.8
        self.color = color
        self.state = self.STAND_STATE
        self.controls = CharacterControls(self)
        radius = max(self.half_width, self.half_height)
        self.body = game_engine.world.CreateDynamicBody(position=(x, y))
        self.body.CreateCircleFixture(radius=radius)
        
    def draw(self):
        glColor3ub(*self.color)
 
        if self.state == self.CROUCH_STATE:
            half_width = 0.4
            half_height = 0.4
        else:
            half_width = self.half_width
            half_height = self.half_height
        min_x = self.x - half_width
        min_y = self.y - half_height
        max_x = self.x + half_width
        max_y = self.y + half_height
        glBegin(GL_POLYGON)
        glVertex2f(min_x, min_y)
        glVertex2f(max_x, min_y)
        glVertex2f(max_x, max_y)
        glVertex2f(min_x, max_y)
        glEnd()

class GameEngine(object):
    def __init__(self, view_width, view_height):
        self._view_width = view_width
        self._view_height = view_height
        self._time = 0.0
        self._world = b2World(gravity=(0.0, -10.0))
        self._actors = set()
        self._step_actors = set()
        self._draw_actors = set()
        self._camera_scale = float(view_height) / 10.0
        self._level_actor = LevelActor(self)
        self._player_actor = CharacterActor(self, x=-3.5, y=-2.75)

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
            actor.step(dt)
        self._world.Step(dt, 10, 10)

    def draw(self):
        glPushMatrix()
        glTranslatef(self._view_width // 2, self._view_height // 2, 0)
        glScalef(self._camera_scale, self._camera_scale, self._camera_scale)
        glTranslatef(-self._player_actor.x, -self._player_actor.y, 0.0)
        for actor in list(self._draw_actors):
            actor.draw()
        glPopMatrix()

    def on_key_press(self, key, modifiers):
        self._player_actor.controls.on_key_press(key, modifiers)

    def on_key_release(self, key, modifiers):
        self._player_actor.controls.on_key_release(key, modifiers)

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
    window = MyWindow()
    pyglet.app.run()

if __name__ == '__main__':
    main()
