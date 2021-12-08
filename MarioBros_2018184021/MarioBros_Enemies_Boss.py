import random

from pico2d import *

from BehaviorTree import BehaviorTree, SelectorNode, SequenceNode, LeafNode

import game_framework
import game_world

import server

from MarioBros_Enemies_Boss_Fire import Fire

# boss Run Speed
PIXEL_PER_METER = (10.0 / 0.3)  # 10 pixel 30 cm
RUN_SPEED_KMPH = 10.0  # Km / Hour
RUN_SPEED_MPM = (RUN_SPEED_KMPH * 1000.0 / 60.0)
RUN_SPEED_MPS = (RUN_SPEED_MPM / 60.0)
RUN_SPEED_PPS = (RUN_SPEED_MPS * PIXEL_PER_METER)

# boss Action Speed
TIME_PER_ACTION = 0.5
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 4

class Boss:
    image = None

    def prepare_patrol_points(self):
        pass

    def __init__(self, left, bottom, width, height, x, y):
        if Boss.image == None:
            Boss.image = load_image('EnemiesAnimationSheet.png')

        # self.prepare_patrol_points()
        # self.patrol_order = 1

        self.left, self.bottom = left, bottom  # clip
        self.width, self.height = width, height
        self.x, self.y = x, y  # 생성 위치

        self.frame = 0

        self.dir = 1
        self.speed = 0
        self.timer = 1.0  # change direction every 1 sec when wandering
        self.wait_timer = 2.0
        self.attack_timer = 2.0

        self.build_behavior_tree()

    def fire_attack(self):
        attack = Fire(self.x, self.y, self.dir * 3)
        game_world.add_object(attack, 1)

    def wander(self):  # 배회
        self.speed = RUN_SPEED_PPS
        self.timer -= game_framework.frame_time
        if self.timer <= 0:
            self.timer = 1.0
            self.dir = random.randint(-1, 1)
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.RUNNING

    def wait(self):
        self.speed = 0
        self.wait_timer -= game_framework.frame_time
        if self.wait_timer <= 0:
            self.wait_timer = 2.0
            return BehaviorTree.SUCCESS

        return BehaviorTree.RUNNING

    def find_player(self):
        distance = (server.mario.x - self.x) ** 2
        if distance < 96759:
            return BehaviorTree.SUCCESS
        else:
            self.speed = 0
            return BehaviorTree.FAIL

    def move_to_player(self):
        self.speed = RUN_SPEED_PPS
        if (server.mario.x - self.x) < 0:  # 플레이어가 보스의 왼쪽에 위치
            self.dir = -1
        else:
            self.dir = 1
        return BehaviorTree.SUCCESS

    def attack_to_player(self):
        distance = (server.mario.x - self.x) ** 2

        if distance < 50000:
            self.speed = 0
            self.attack_timer -= game_framework.frame_time
            if self.attack_timer <= 0:
                attack = Fire(self.x, self.y, self.dir * 3)
                game_world.add_object(attack, 1)
                self.attack_timer = 2.0
            return BehaviorTree.SUCCESS
        else:
            self.speed = 0
            return BehaviorTree.FAIL


    def build_behavior_tree(self):
        wander_node = LeafNode("Wander", self.wander)
        find_player_node = LeafNode("Find Player", self.find_player)
        move_to_player_node = LeafNode("Move to Player", self.move_to_player)
        attack_to_player_node = LeafNode("Attack to Player", self.attack_to_player)

        chase_node = SequenceNode("Chase")
        chase_node.add_children(find_player_node, move_to_player_node, attack_to_player_node)

        wander_chase_node = SelectorNode("WanderChase")
        wander_chase_node.add_children(chase_node, wander_node)

        self.bt = BehaviorTree(wander_chase_node)

    def get_bb(self):
        from MarioBros_Mario import Move_locX
        return self.x - Move_locX - 20, self.y - 13, self.x - Move_locX + 20, self.y + 13

    def update(self):
        self.bt.run()

        if self.dir == 1:  # 오른쪽
            self.left = 160
            self.frame = (self.frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % FRAMES_PER_ACTION
        elif self.dir == -1:
            self.left = 120
            self.frame = -((self.frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % FRAMES_PER_ACTION)

        self.x += self.speed * game_framework.frame_time * self.dir
        self.x = clamp(2050, self.x, 2830)

    def draw(self):
        from MarioBros_Mario import Move_locX
        self.image.clip_draw(self.left + int(self.frame) * 40, self.bottom, self.width, self.height, self.x - Move_locX, self.y)

        # draw_rectangle(*self.get_bb())
