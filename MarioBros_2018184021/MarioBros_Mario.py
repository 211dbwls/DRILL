from pico2d import *
import random

import game_framework
import game_world

from MarioBros_Mario_FireBall import FireBall

history = []  # (현재 상태, 이벤트) 저장하는 리스트

RIGHT_DOWN, LEFT_DOWN, JUMP_DOWN, RIGHT_UP, LEFT_UP, JUMP_UP, SPACE, DEBUG_KEY = range(8)

event_name = ['RIGHT_DOWN', 'LEFT_DOWN', 'JUMP_DOWN', 'RIGHT_UP', 'LEFT_UP', 'JUMP_UP', 'SPACE', 'DEBUG_KEY']

key_event_table = {
    (SDL_KEYDOWN, SDLK_d): RIGHT_DOWN,
    (SDL_KEYDOWN, SDLK_a): LEFT_DOWN,
    (SDL_KEYDOWN, SDLK_w): JUMP_DOWN,
    (SDL_KEYUP, SDLK_d): RIGHT_UP,
    (SDL_KEYUP, SDLK_a): LEFT_UP,
    (SDL_KEYUP, SDLK_w): JUMP_UP,
    (SDL_KEYUP, SDLK_SPACE): SPACE,

    (SDL_KEYDOWN, SDLK_q): DEBUG_KEY
}

# 마리오 달리기 속도
PIXEL_PER_METER = (30.0 / 0.9)  # 30 pixel 90 cm (1 pixel 3 cm)
RUN_SPEED_KMPH = 5.0
RUN_SPEED_MPM = (RUN_SPEED_KMPH * 1000.0 / 60.0)
RUN_SPEED_MPS = (RUN_SPEED_MPM / 60.0)
RUN_SPEED_PPS = (RUN_SPEED_MPS * PIXEL_PER_METER)  # 초당 이동하는 픽셀 수


# 마리오 액션 속도
TIME_PER_ACTION = 0.5
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 3
FRAMES_PER_ACTION_JUMP = 6

Mario_jumping = False

Move_locX = 0

Mario_coins = 0
Mario_score = 0
Mario_life = 3

class IdleState:
    def enter(self, event):
        if event == RIGHT_DOWN:
            self.velocity += RUN_SPEED_PPS
        elif event == LEFT_DOWN:
            self.velocity -= RUN_SPEED_PPS
        elif event == RIGHT_UP:
            self.velocity -= RUN_SPEED_PPS
        elif event == LEFT_UP:
            self.velocity += RUN_SPEED_PPS

    def exit(self, event):
        if event == SPACE:
            self.fire_ball()

    def do(self):
        self.y -= self.gravity * game_framework.frame_time

    def draw(self):
        self.image.clip_draw(self.left, self.bottom, self.width, self.height, self.x - Move_locX, self.y)

class RunState:
    def enter(self, event):
        if event == RIGHT_DOWN:
            self.velocity += RUN_SPEED_PPS
        elif event == LEFT_DOWN:
            self.velocity -= RUN_SPEED_PPS
        elif event == RIGHT_UP:
            self.velocity -= RUN_SPEED_PPS
        elif event == LEFT_UP:
            self.velocity += RUN_SPEED_PPS

        self.dir = clamp(-1, self.velocity, 1)
        if self.dir == 0:
            self.dir = 1

        global FRAMES_PER_ACTION
        FRAMES_PER_ACTION = 3


    def exit(self, event):
        if event == SPACE:
            self.fire_ball()

    def do(self):
        if self.dir == 1:  # 오른쪽으로 이동 중일 경우 애니메이션 설정
            self.left = self.move_right_frame
            self.frame = (self.frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % FRAMES_PER_ACTION
            # print("dir : 1 frame : " + str(self.frame))
        elif self.dir == -1:  # 왼쪽으로 이동 중일 경우 애니메이션 설정
            self.left = self.move_left_frame
            self.frame = -((self.frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % FRAMES_PER_ACTION)
            # print("dir : -1 frame : " + str(self.frame))
        self.x += self.velocity * game_framework.frame_time
        self.x = clamp(25, self.x, 3600)

    def draw(self):
        self.image.clip_draw(self.left + int(self.frame) * self.width, self.bottom, self.width, self.height, self.x - Move_locX, self.y)

class JumpState:
    def enter(self, event):
        if event == RIGHT_DOWN:
            self.velocity += RUN_SPEED_PPS
        elif event == LEFT_DOWN:
            self.velocity -= RUN_SPEED_PPS
        elif event == RIGHT_UP:
            self.velocity -= RUN_SPEED_PPS
        elif event == LEFT_UP:
            self.velocity += RUN_SPEED_PPS

        global Mario_jumping
        Mario_jumping = True

        global FRAMES_PER_ACTION
        FRAMES_PER_ACTION = 6

        self.gravity = 50
        self.jump_height = 0

        self.sound_jump()

    def exit(self, event):
        if event == SPACE:
            self.fire_ball()

    def do(self):
        # global Mario_jumping
        # if Mario_jumping == True:
        #     self.jump_height += 10
        #     if self.jump_height == 100:
        #         Mario_jumping = False
        # else:
        #     self.jump_height -= 10
        #     self.jump_height = clamp(0, self.jump_height, 100)

        if self.dir == 1:  # 오른쪽으로 이동 중일 경우 애니메이션 설정
            self.left = self.move_right_frame
            self.frame = (self.frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % FRAMES_PER_ACTION
        elif self.dir == -1:  # 왼쪽으로 이동 중일 경우 애니메이션 설정
            self.left = self.move_left_frame
            self.frame = -((self.frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % FRAMES_PER_ACTION)
        self.x += self.velocity * game_framework.frame_time
        self.x = clamp(25, self.x, 3600)

        if self.jump_height < 30:
            self.y += self.gravity * game_framework.frame_time
            self.jump_height += self.gravity * game_framework.frame_time
        else:
            global Mario_jumping
            Mario_jumping = False


    def draw(self):
        self.image.clip_draw(self.left + int(self.frame) * self.width, self.bottom, self.width, self.height, self.x - Move_locX, self.y + self.jump_height)

next_state_table = {
    IdleState: {RIGHT_UP: RunState, LEFT_UP: RunState, JUMP_UP: JumpState,
                RIGHT_DOWN: RunState, LEFT_DOWN: RunState, JUMP_DOWN: JumpState, SPACE: IdleState},
    RunState: {RIGHT_UP: IdleState, LEFT_UP: IdleState, JUMP_UP: JumpState,
               LEFT_DOWN: IdleState, RIGHT_DOWN: IdleState, JUMP_DOWN: JumpState, SPACE: RunState},
    JumpState: {RIGHT_UP: RunState, LEFT_UP: RunState, JUMP_UP: IdleState,
               LEFT_DOWN: RunState, RIGHT_DOWN: RunState, JUMP_DOWN: IdleState, SPACE: JumpState}
}

class Mario:  # 마리오
    image = None

    def __init__(self, Start_locX, Start_locY):
        if Mario.image == None:
            Mario.image = load_image('MarioAnimationSheet.png')

        self.left, self.bottom = 200, 170
        self.width, self.height = 30, 30

        self.x, self.y = Start_locX, Start_locY  # 30

        self.dir = 1
        self.velocity = 0  # 속도
        self.gravity = 50
        self.jump_height = 0

        self.move_right_frame, self.move_left_frame = 200, 170
        self.frame = 0  # 애니메이션 프레임

        self.event_que = []

        self.cur_state = IdleState
        self.cur_state.enter(self, None)

        self.mario_in_bonusstage = False

        self.parent = None

        # 배경 사운드
        self.bgm = load_wav('Sound_main theme overworld.wav')
        self.bgm.set_volume(40)  # 소리 크리 0 ~ 128
        self.bgm.repeat_play()  # 반복 재생
        # 점프 사운드
        self.jump_sound = load_wav('Sound_Jumps.wav')
        self.jump_sound.set_volume(44)
        # 공격 사운드
        self.attack_sound = load_wav('Sound_fire ball.wav')
        self.attack_sound.set_volume(44)
        # 코인 획득 사운드
        self.question_box_coin_sound = load_wav('Sound_gets a coin.wav')
        self.question_box_coin_sound.set_volume(44)
        # 떨어질 때 사운드
        self.falling_down_sound = load_wav('Sound_Dies.wav')
        self.falling_down_sound.set_volume(44)
        # 성에 들어갈 때 사운드
        self.into_castle_sound = load_wav('Sound_castle complete.wav')
        self.into_castle_sound.set_volume(44)
        # 게임 종료 사운드
        self.gameover_sound = load_wav('Sound_you re dead.wav')
        self.gameover_sound.set_volume(44)

    def changeBigMario(self):  # 큰 마리오
        self.bottom = 100
        self.height = 37
        self.y += 10

    def changeFireMario(self):  # 불 마리오
        self.bottom = 30
        self.width, self.height = 25, 37
        self.move_right_frame, self.move_left_frame = 230, 175

    # 공격
    def fire_ball(self):
        fireball = FireBall(self.x, self.y, self.dir * 3)
        self.attack_sound.play()
        game_world.add_object(fireball, 1)

    # 사운드
    def sound_jump(self):
        self.jump_sound.play()

    def sound_into_castle(self):
        self.into_castle_sound.play()

    def sound_stop_bgm(self):
        self.bgm.set_volume(0)

    def add_event(self, event):
        self.event_que.insert(0, event)

    # 충돌 체크
    def get_bb(self):
        return self.x - Move_locX - 10, self.y - 15, self.x - Move_locX + 10, self.y + 15

    def get_bb_foot(self):
        return self.x - Move_locX - 5, self.y - 15, self.x - Move_locX + 10, self.y - 5

    def get_bb_head(self):
        return self.x - Move_locX - 5, self.y + 10, self.x - Move_locX + 10, self.y + 15

    # 충돌 처리 - 코인 : 코인 개수 추가
    def addCoin(self):
        global Mario_coins
        Mario_coins += 1
        self.question_box_coin_sound.play()
    # 충돌 처리 - 점수 추가
    def addScore(self, score):
        global Mario_score
        Mario_score += score
    # 충돌 처리 - 목숨
    def addLife(self):
        global Mario_life
        Mario_life += 1
    def minusLife(self):
        global Mario_life
        Mario_life -= 1
        Mario_life = clamp(-1, Mario_life, 100)

    # 충돌 처리 - 좌우로 이동 못하도록
    def cantgo_left(self, collide_loc):
        if self.x > collide_loc:
            self.x = collide_loc
    def cantgo_right(self, collide_loc):
        if self.x < collide_loc:
            self.x = collide_loc
    # 충돌 처리 - 아래로 떨어지지 않도록
    def stop(self, collide_loc):
        if self.y < collide_loc:
            self.y = collide_loc

    # 떨어졌을 경우
    def falling_died(self):
        global Mario_life
        Mario_life -= 1
        self.falling_down_sound.play()

    def set_parent(self, ground):
        self.parent = ground
        self.y = ground.y + ground.MARIO_Y0

    def update(self):
        if Mario_life == 0:
            self.sound_stop_bgm()
            self.gameover_sound.play()
            delay(4)
            game_framework.quit()

        self.cur_state.do(self)

        if len(self.event_que) > 0:
            event = self.event_que.pop()
            self.cur_state.exit(self, event)  # 현재 상태 나감

            # error occurs here
            try:  # 시도를 해본다.
                history.append((self.cur_state.__name__, event_name[event]))  # (현재 상태, 이벤트) 튜플 저장
                self.cur_state = next_state_table[self.cur_state][event]
            except:  # 문제 발생 확인
                print('State : ' + self.cur_state.__name__ + ' event : ' + event_name[event])  # 현재 상태와 이벤트 출력
                exit(-1)

            self.cur_state.enter(self, event)  # 결정한 다음 상태 진행

    def draw(self):
        global Move_locX, Mario_in_BonusStage

        if self.mario_in_bonusstage == False:
            if self.x >= 400:  # 일정 거리를 넘으면 맵이 움직이도록
                Move_locX = self.x - 400
            if self.x >= 3200:  # 일정 거리를 넘으면 맵이 움직이지 않도록
                Move_locX = 3200 - 400
        else:
            Move_locX = 0

        self.cur_state.draw(self)

        debug_print('Velocity : ' + str(self.velocity) + ' Dir : ' + str(self.dir))

        # print("Mario : " + str(self.x) + "  " + str(self.y))

        # draw_rectangle(*self.get_bb())
        # draw_rectangle(*self.get_bb_foot())
        # draw_rectangle(*self.get_bb_head())

    def handle_event(self, event):
       if(event.type, event.key) in key_event_table:
           key_event = key_event_table[(event.type, event.key)]
           if DEBUG_KEY == key_event:  # history 출력_디버그
               print(history[-10:])
           else:
               self.add_event(key_event)
