"""
============================================================
  DISEGNA & ANIMA PRO — v1.0 RELEASE UFFICIALE
  Mobile First • Pydroid/Android • UI touch-friendly
  Modificato per compatibilità Android
============================================================
"""

import pygame
import sys
import math
import os
import json
import random
from datetime import datetime

# IMPORTANTE per Android: prima di pygame.init()
os.environ['SDL_MOUSE_TOUCHID'] = '0'

# Rileva se siamo su Android
IS_ANDROID = 'ANDROID_ARGUMENT' in os.environ

# Directory sicura per salvataggi (funziona su tutte le piattaforme)
APP_DIR = os.path.dirname(os.path.abspath(__file__))

pygame.init()

VERSION = "1.0"

# ─── COLORI AGGIORNATI ─────────────────────────────────
C_BG        = (18, 18, 26)
C_PANEL     = (32, 32, 42)
C_PANEL_L   = (45, 45, 58)
C_ACCENT    = (0, 190, 255)
C_ACCENT2   = (255, 90, 120)
C_TEXT      = (240, 240, 250)
C_TEXT_DIM  = (150, 150, 165)
C_WHITE     = (255, 255, 255)
C_BLACK     = (10, 10, 14)
C_GREEN     = (70, 220, 120)
C_RED       = (255, 85, 85)
C_YELLOW    = (255, 200, 50)
C_PURPLE    = (160, 80, 200)
C_ORANGE    = (255, 150, 50)
C_ONION     = (120, 120, 130)

COLORS = [C_BLACK, C_RED, C_ACCENT, C_GREEN, C_YELLOW, C_PURPLE, C_ORANGE, C_WHITE, (255,100,180), (160,120,80)]

# Cache font globale (evita ricreazione ogni frame)
_font_cache = {}
def get_font(size):
    if size not in _font_cache:
        try:
            _font_cache[size] = pygame.font.SysFont("arial", size)
        except:
            _font_cache[size] = pygame.font.Font(None, size)
    return _font_cache[size]

class Vec2:
    __slots__ = ('x','y')
    def __init__(self, x=0.0, y=0.0):
        self.x, self.y = float(x), float(y)
    def __add__(self, o): return Vec2(self.x+o.x, self.y+o.y)
    def __sub__(self, o): return Vec2(self.x-o.x, self.y-o.y)
    def __mul__(self, s): return Vec2(self.x*s, self.y*s)
    def copy(self): return Vec2(self.x, self.y)
    def dist(self, o): return math.hypot(self.x-o.x, self.y-o.y)
    def to_int(self): return (int(self.x), int(self.y))
    def to_list(self): return [self.x, self.y]
    @staticmethod
    def from_list(lst): return Vec2(lst[0], lst[1])

class StickmanJoint:
    __slots__ = ('name','pos','old_pos','pinned','radius')
    def __init__(self, name, x, y, pinned=False):
        self.name = name
        self.pos = Vec2(x, y)
        self.old_pos = Vec2(x, y)
        self.pinned = pinned
        self.radius = 6
    def update_physics(self, gravity=Vec2(0,0.4), damping=0.98, floor_y=9999):
        if self.pinned:
            self.old_pos = self.pos.copy(); return
        vel = (self.pos - self.old_pos) * damping
        self.old_pos = self.pos.copy()
        self.pos = self.pos + vel + gravity
        if self.pos.y > floor_y - self.radius:
            self.pos.y = floor_y - self.radius
            vel = self.pos - self.old_pos
            self.old_pos = Vec2(self.old_pos.x, self.pos.y + vel.y * 0.3)
    def set_pos(self, x, y):
        self.pos = Vec2(x, y); self.old_pos = Vec2(x, y)

class StickmanDynamic:
    def __init__(self, cx, cy, scale=1.0):
        self.scale = scale
        self.joints = {}
        self.constraints = []
        self.detached = set()
        self.selected_joint = None
        self.dragged_joint = None
        self.wobble_phase = 0.0
        self._init_pose(cx, cy)
        self._build_constraints()
        self.ground_y = 9999

    def _init_pose(self, cx, cy):
        s = self.scale
        defs = {"pelvis":(0,10),"neck":(0,-45),"head":(0,-70),
            "l_shoulder":(-20,-40),"l_elbow":(-35,-15),"l_hand":(-50,10),
            "r_shoulder":(20,-40),"r_elbow":(35,-15),"r_hand":(50,10),
            "l_hip":(-15,15),"l_knee":(-20,50),"l_foot":(-25,85),
            "r_hip":(15,15),"r_knee":(20,50),"r_foot":(25,85)}
        for name, (dx,dy) in defs.items():
            self.joints[name] = StickmanJoint(name, cx+dx*s, cy+dy*s)
        self.joints["pelvis"].pinned = True

    def _build_constraints(self):
        self.constraints = []
        pairs = [("neck","head"),("neck","pelvis"),("neck","l_shoulder"),("l_shoulder","l_elbow"),("l_elbow","l_hand"),
            ("neck","r_shoulder"),("r_shoulder","r_elbow"),("r_elbow","r_hand"),("pelvis","l_hip"),("l_hip","l_knee"),("l_knee","l_foot"),
            ("pelvis","r_hip"),("r_hip","r_knee"),("r_knee","r_foot")]
        for a,b in pairs:
            if a in self.joints and b in self.joints:
                self.constraints.append([a,b,self.joints[a].pos.dist(self.joints[b].pos),True])

    def resize(self, factor):
        cx, cy = self.joints["pelvis"].pos.x, self.joints["pelvis"].pos.y
        self.scale *= factor
        for j in self.joints.values():
            if j.name != "pelvis":
                j.set_pos(cx + (j.pos.x-cx)*factor, cy + (j.pos.y-cy)*factor)
                j.old_pos = j.pos.copy()
        self._build_constraints()

    def toggle_detached(self, joint_name):
        if joint_name in self.detached:
            self.detached.discard(joint_name)
            for c in self.constraints:
                if c[0]==joint_name or c[1]==joint_name: c[3]=True
            self._reattach_ik(joint_name)
            return False
        else:
            self.detached.add(joint_name)
            for c in self.constraints:
                if c[0]==joint_name or c[1]==joint_name: c[3]=False
            return True

    def _reattach_ik(self, jn):
        pmap = {"head":"neck","l_elbow":"l_shoulder","l_hand":"l_elbow","r_elbow":"r_shoulder","r_hand":"r_elbow",
                "l_knee":"l_hip","l_foot":"l_knee","r_knee":"r_hip","r_foot":"r_knee"}
        if jn in pmap:
            p, j = self.joints[pmap[jn]], self.joints[jn]
            for c in self.constraints:
                if (c[0]==pmap[jn] and c[1]==jn) or (c[1]==pmap[jn] and c[0]==jn):
                    d = c[2]; ang = math.atan2(j.pos.y-p.pos.y, j.pos.x-p.pos.x)
                    j.set_pos(p.pos.x+math.cos(ang)*d, p.pos.y+math.sin(ang)*d); break

    def set_ragdoll(self, active):
        self.joints["pelvis"].pinned = not active
        if active:
            for j in self.joints.values(): j.old_pos.x += random.uniform(-1,1)

    def update_physics(self, gravity=Vec2(0,0.5), iterations=3):
        for j in self.joints.values(): j.update_physics(gravity, 0.97, self.ground_y)
        for _ in range(iterations):
            for c in self.constraints:
                a_name, b_name, rest_len, active = c
                if not active: continue
                ja, jb = self.joints[a_name], self.joints[b_name]
                dx, dy = jb.pos.x-ja.pos.x, jb.pos.y-ja.pos.y
                dist = math.hypot(dx, dy)
                if dist < 0.001: continue
                diff = (dist - rest_len) / dist
                if ja.pinned and not jb.pinned:
                    jb.pos.x -= dx*diff; jb.pos.y -= dy*diff
                elif jb.pinned and not ja.pinned:
                    ja.pos.x += dx*diff; ja.pos.y += dy*diff
                elif not ja.pinned and not jb.pinned:
                    ox, oy = dx*diff*0.5, dy*diff*0.5
                    ja.pos.x += ox; ja.pos.y += oy
                    jb.pos.x -= ox; jb.pos.y -= oy
        for name in ("l_foot","r_foot"):
            j = self.joints[name]
            if j.pos.y > self.ground_y - 5: j.pos.y = self.ground_y - 5

    def update_joint_pos(self, j_name, new_pos, luffy_mode=False, ragdoll_mode=False):
        if j_name not in self.joints: return
        j = self.joints[j_name]
        if ragdoll_mode:
            j.pos = Vec2(new_pos[0], new_pos[1]); j.old_pos = j.pos.copy(); return
        if luffy_mode or j_name in self.detached:
            j.set_pos(new_pos[0], new_pos[1]); return
        if j_name in ("l_hand","r_hand","l_foot","r_foot"):
            self._solve_ik_for(j_name, new_pos)
        elif j_name in ("head","neck"):
            self._rotate_spine(new_pos)
        elif j_name in ("l_elbow","r_elbow","l_knee","r_knee"):
            j.set_pos(new_pos[0], new_pos[1])
            child = {"l_elbow":"l_hand","r_elbow":"r_hand","l_knee":"l_foot","r_knee":"r_foot"}.get(j_name)
            if child: self._solve_ik_for(child, self.joints[child].pos.to_list())
        else:
            j.set_pos(new_pos[0], new_pos[1])

    def _solve_ik_for(self, tip_name, target):
        pmap = {"l_hand":("l_shoulder","l_elbow","l_hand"),"r_hand":("r_shoulder","r_elbow","r_hand"),
                "l_foot":("l_hip","l_knee","l_foot"),"r_foot":("r_hip","r_knee","r_foot")}
        if tip_name not in pmap: return
        root_name, mid_name, tip = pmap[tip_name]
        root, mid, tip_j = self.joints[root_name], self.joints[mid_name], self.joints[tip]
        l1 = self._get_rest_len(root_name, mid_name)
        l2 = self._get_rest_len(mid_name, tip)
        if l1 is None or l2 is None: tip_j.set_pos(target[0], target[1]); return
        rx, ry = root.pos.x, root.pos.y
        tx, ty = target[0], target[1]
        dx, dy = tx-rx, ty-ry
        dist = math.hypot(dx, dy)
        max_d = (l1+l2)*0.999
        if dist > max_d: tx = rx + (dx/dist)*max_d; ty = ry + (dy/dist)*max_d; dist = max_d
        min_d = abs(l1-l2)*1.001
        if dist < min_d: dist = min_d
        ca = max(-1.0, min(1.0, (l1**2 + dist**2 - l2**2)/(2*l1*dist)))
        ao = math.acos(ca)
        ba = math.atan2(ty-ry, tx-rx)
        bend = -1 if "l_" in tip else 1
        if "foot" in tip: bend *= -1
        ja = ba + ao * bend
        mid.set_pos(rx + l1*math.cos(ja), ry + l1*math.sin(ja))
        tip_j.set_pos(tx, ty)

    def _get_rest_len(self, a, b):
        for c in self.constraints:
            if (c[0]==a and c[1]==b) or (c[0]==b and c[1]==a): return c[2]
        return None

    def _rotate_spine(self, new_pos):
        pelvis = self.joints["pelvis"]
        dx, dy = new_pos[0]-pelvis.pos.x, new_pos[1]-pelvis.pos.y
        dist = math.hypot(dx, dy)
        spine = self._get_rest_len("pelvis","neck")
        if spine is None: spine = 55*self.scale
        if dist > 0:
            nk = self.joints["neck"]
            nk.set_pos(pelvis.pos.x + (dx/dist)*spine, pelvis.pos.y + (dy/dist)*spine)
            nx, ny = nk.pos.x, nk.pos.y
            sw = self._get_rest_len("neck","l_shoulder")
            if sw is None: sw = 20*self.scale
            nh = self._get_rest_len("neck","head")
            if nh is None: nh = 25*self.scale
            self.joints["head"].set_pos(nx, ny-nh)
            self.joints["l_shoulder"].set_pos(nx-sw, ny+5*self.scale)
            self.joints["r_shoulder"].set_pos(nx+sw, ny+5*self.scale)

    def get_joint_at(self, pos, radius=25):
        best, best_d = None, radius
        pv = Vec2(pos[0], pos[1])
        for name, j in self.joints.items():
            d = j.pos.dist(pv)
            if d < best_d: best_d = d; best = name
        return best

    def draw(self, surf, color, show_joints=False, is_selected=False, luffy_mode=False, theme_dark=True):
        base_col = C_RED if (is_selected and not show_joints) else color
        det_col = C_PURPLE
        gum_col = (255, 180, 60)
        if not theme_dark:
            for c in self.constraints:
                if not c[3]: continue
                j1, j2 = self.joints[c[0]], self.joints[c[1]]
                pygame.draw.line(surf, (200,200,210), (j1.pos.x+2,j1.pos.y+2), (j2.pos.x+2,j2.pos.y+2), max(2,int(3*self.scale)))
        for c in self.constraints:
            if not c[3]: continue
            j1, j2 = self.joints[c[0]], self.joints[c[1]]
            p1, p2 = j1.pos.to_int(), j2.pos.to_int()
            is_det = (c[0] in self.detached or c[1] in self.detached)
            line_col = det_col if is_det else base_col
            lw = max(2, int(4*self.scale))
            actual = j1.pos.dist(j2.pos); rest = c[2]
            if luffy_mode and actual > rest*1.3 and not is_det:
                mid = (j1.pos + j2.pos) * 0.5
                dx, dy = j2.pos.x-j1.pos.x, j2.pos.y-j1.pos.y
                perp = Vec2(-dy, dx); plen = math.hypot(perp.x, perp.y)
                if plen > 0:
                    stretch = (actual/rest)-1.0
                    wobble = math.sin(self.wobble_phase + actual*0.1)*15*stretch
                    perp = perp * (wobble/plen)
                ctrl = mid + perp
                pts = []
                for t in range(0, 11):
                    t = t/10.0
                    x = (1-t)**2*j1.pos.x + 2*(1-t)*t*ctrl.x + t**2*j2.pos.x
                    y = (1-t)**2*j1.pos.y + 2*(1-t)*t*ctrl.y + t**2*j2.pos.y
                    pts.append((x,y))
                if len(pts)>1:
                    pygame.draw.lines(surf, gum_col, False, pts, lw)
                    pygame.draw.lines(surf, (200,140,30), False, pts, 1)
            else:
                pygame.draw.line(surf, line_col, p1, p2, lw)
        head = self.joints["head"]
        hr = max(4, int(14*self.scale))
        hc = det_col if "head" in self.detached else base_col
        if luffy_mode and "head" not in self.detached:
            pygame.draw.ellipse(surf, gum_col, (head.pos.x-hr, head.pos.y-int(hr*1.1), hr*2, int(hr*2.2)), max(2,int(3*self.scale)))
        else:
            pygame.draw.circle(surf, hc, head.pos.to_int(), hr, max(1,int(3*self.scale)))
        if show_joints and is_selected:
            for name, j in self.joints.items():
                dr = 7 if name==self.selected_joint else 5
                col = C_RED if name==self.selected_joint else C_ACCENT
                if name in self.detached: col = C_PURPLE
                pygame.draw.circle(surf, col, j.pos.to_int(), dr)

# ─── ICONE ──────────────────────────────────────────────
class Icon:
    @staticmethod
    def pen(s, r, c):
        cx, cy = r.center
        pygame.draw.polygon(s, c, [(cx-4,cy+4),(cx+1,cy-4),(cx+4,cy-1),(cx-1,cy+4)])
    @staticmethod
    def eraser(s, r, c):
        pygame.draw.rect(s, c, (r.centerx-5, r.centery-3, 10, 6), border_radius=1)
    @staticmethod
    def hand(s, r, c):
        cx, cy = r.center
        pygame.draw.circle(s, c, (cx, cy-1), 3)
        pygame.draw.line(s, c, (cx, cy+2), (cx, cy+7), 2)
    @staticmethod
    def line(s, r, c):
        pygame.draw.line(s, c, (r.centerx-5, r.centery+3), (r.centerx+5, r.centery-3), 2)
    @staticmethod
    def circle(s, r, c):
        pygame.draw.circle(s, c, r.center, 5, 2)
    @staticmethod
    def rect(s, r, c):
        pygame.draw.rect(s, c, (r.centerx-4, r.centery-4, 8, 8), 2)
    @staticmethod
    def fill(s, r, c):
        cx, cy = r.center
        pygame.draw.polygon(s, c, [(cx-4, cy-2), (cx+4, cy-2), (cx, cy+4)])
    @staticmethod
    def text(s, r, c):
        cx, cy = r.center
        pygame.draw.line(s, c, (cx-3, cy-4), (cx+3, cy-4), 2)
        pygame.draw.line(s, c, (cx-3, cy), (cx+3, cy), 2)
    @staticmethod
    def stickman(s, r, c):
        cx, cy = r.center
        pygame.draw.circle(s, c, (cx, cy-4), 2, 1)
        pygame.draw.line(s, c, (cx, cy-1), (cx, cy+3), 2)
        pygame.draw.line(s, c, (cx, cy+1), (cx-3, cy+4), 1)
        pygame.draw.line(s, c, (cx, cy+1), (cx+3, cy+4), 1)
    @staticmethod
    def play(s, r, c):
        pygame.draw.polygon(s, c, [(r.centerx-3, r.centery-4), (r.centerx-3, r.centery+4), (r.centerx+4, r.centery)])
    @staticmethod
    def pause(s, r, c):
        pygame.draw.rect(s, c, (r.centerx-4, r.centery-4, 2, 8))
        pygame.draw.rect(s, c, (r.centerx+2, r.centery-4, 2, 8))
    @staticmethod
    def star(s, r, c):
        pts = []
        for i in range(10):
            a = math.pi/2 + i*math.pi/5
            rr = 6 if i%2==0 else 2
            pts.append((r.centerx+rr*math.cos(a), r.centery-rr*math.sin(a)))
        pygame.draw.polygon(s, c, pts, 1)
    @staticmethod
    def triangle(s, r, c):
        pygame.draw.polygon(s, c, [(r.centerx, r.centery-5), (r.centerx-5, r.centery+4), (r.centerx+5, r.centery+4)], 2)
    @staticmethod
    def zoom_in(s, r, c):
        pygame.draw.circle(s, c, r.center, 5, 1)
        pygame.draw.line(s, c, (r.centerx-3, r.centery), (r.centerx+3, r.centery), 2)
        pygame.draw.line(s, c, (r.centerx, r.centery-3), (r.centerx, r.centery+3), 2)
    @staticmethod
    def zoom_out(s, r, c):
        pygame.draw.circle(s, c, r.center, 5, 1)
        pygame.draw.line(s, c, (r.centerx-3, r.centery), (r.centerx+3, r.centery), 2)
    @staticmethod
    def grid(s, r, c):
        for i in (-3, 0, 3):
            pygame.draw.line(s, c, (r.centerx+i, r.centery-5), (r.centerx+i, r.centery+5), 1)
            pygame.draw.line(s, c, (r.centerx-5, r.centery+i), (r.centerx+5, r.centery+i), 1)
    @staticmethod
    def onion(s, r, c):
        pygame.draw.ellipse(s, c, (r.centerx-5, r.centery-6, 10, 12), 1)
        pygame.draw.ellipse(s, c, (r.centerx-3, r.centery-4, 6, 8), 1)
    @staticmethod
    def undo(s, r, c):
        cx, cy = r.center
        pygame.draw.arc(s, c, (cx-5, cy-5, 10, 10), math.pi/2, math.pi*2, 2)
        pygame.draw.polygon(s, c, [(cx-5, cy-2), (cx-2, cy-5), (cx-2, cy+1)])
    @staticmethod
    def save(s, r, c):
        pygame.draw.rect(s, c, (r.centerx-4, r.centery-5, 8, 10), 2, border_radius=1)
        pygame.draw.line(s, c, (r.centerx-2, r.centery-5), (r.centerx-2, r.centery-2), 2)
    @staticmethod
    def export(s, r, c):
        pygame.draw.rect(s, c, (r.centerx-4, r.centery-3, 8, 7), 2, border_radius=1)
        pygame.draw.polygon(s, c, [(r.centerx, r.centery+2), (r.centerx-2, r.centery+5), (r.centerx+2, r.centery+5)])
    @staticmethod
    def settings(s, r, c):
        cx, cy = r.center
        for i in range(8):
            a = i * math.pi / 4
            x1 = cx + 3*math.cos(a); y1 = cy + 3*math.sin(a)
            x2 = cx + 6*math.cos(a); y2 = cy + 6*math.sin(a)
            pygame.draw.line(s, c, (x1, y1), (x2, y2), 2)
        pygame.draw.circle(s, c, (cx, cy), 2, 1)
    @staticmethod
    def add(s, r, c):
        pygame.draw.line(s, c, (r.centerx-5, r.centery), (r.centerx+5, r.centery), 2)
        pygame.draw.line(s, c, (r.centerx, r.centery-5), (r.centerx, r.centery+5), 2)
    @staticmethod
    def luffy(s, r, c):
        pygame.draw.ellipse(s, c, (r.centerx-4, r.centery-6, 8, 12), 2)
    @staticmethod
    def ragdoll(s, r, c):
        pygame.draw.circle(s, c, (r.centerx, r.centery-3), 3, 1)
        pygame.draw.line(s, c, (r.centerx, r.centery), (r.centerx-3, r.centery+5), 1)
        pygame.draw.line(s, c, (r.centerx, r.centery), (r.centerx+3, r.centery+5), 1)
    @staticmethod
    def detach(s, r, c):
        pygame.draw.line(s, c, (r.centerx-5, r.centery), (r.centerx-1, r.centery), 2)
        pygame.draw.line(s, c, (r.centerx+1, r.centery), (r.centerx+5, r.centery), 2)
        pygame.draw.circle(s, c, (r.centerx, r.centery), 3)
    @staticmethod
    def resize_up(s, r, c):
        pygame.draw.rect(s, c, (r.centerx-3, r.centery-3, 6, 6), 1)
        pygame.draw.line(s, c, (r.centerx-5, r.centery-5), (r.centerx-2, r.centery-2), 2)
    @staticmethod
    def resize_down(s, r, c):
        pygame.draw.rect(s, c, (r.centerx-3, r.centery-3, 6, 6), 1)
        pygame.draw.line(s, c, (r.centerx+2, r.centery+2), (r.centerx+5, r.centery+5), 2)
    @staticmethod
    def reset(s, r, c):
        pygame.draw.circle(s, c, r.center, 4, 1)
        pygame.draw.polygon(s, c, [(r.centerx+3, r.centery-4), (r.centerx+6, r.centery-1), (r.centerx+3, r.centery+2)])
    @staticmethod
    def arrow_right(s, r, c):
        pygame.draw.polygon(s, c, [(r.centerx-3, r.centery-5), (r.centerx-3, r.centery+5), (r.centerx+5, r.centery)])
    @staticmethod
    def arrow_left(s, r, c):
        pygame.draw.polygon(s, c, [(r.centerx+3, r.centery-5), (r.centerx+3, r.centery+5), (r.centerx-5, r.centery)])
    @staticmethod
    def menu(s, r, c):
        for i, y in enumerate((r.centery-4, r.centery, r.centery+4)):
            pygame.draw.line(s, c, (r.centerx-5, y), (r.centerx+5, y), 2)
    @staticmethod
    def close(s, r, c):
        pygame.draw.line(s, c, (r.centerx-4, r.centery-4), (r.centerx+4, r.centery+4), 2)
        pygame.draw.line(s, c, (r.centerx+4, r.centery-4), (r.centerx-4, r.centery+4), 2)
    @staticmethod
    def rotate(s, r, c):
        cx, cy = r.center
        pygame.draw.line(s, c, (cx-6, cy-4), (cx+6, cy+4), 2)
        pygame.draw.polygon(s, c, [(cx+4, cy+2), (cx+6, cy+6), (cx+2, cy+4)])

ICONS = {k: getattr(Icon, k) for k in [
    "pen","eraser","hand","line","circle","rect","fill","text","stickman",
    "play","pause","star","triangle","zoom_in","zoom_out","grid","onion",
    "undo","save","export","settings","add","luffy","ragdoll","detach",
    "resize_up","resize_down","reset","arrow_right","arrow_left","menu","close","rotate"
]}

# ─── APP PRINCIPALE ─────────────────────────────────────
class App:
    def __init__(self):
        # Inizializzazione schermo adattiva
        if IS_ANDROID:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.w, self.h = self.screen.get_size()
        else:
            info = pygame.display.Info()
            self.w = info.current_w if info.current_w > 0 else 1280
            self.h = info.current_h if info.current_h > 0 else 720
            self.screen = pygame.display.set_mode((self.w, self.h), pygame.RESIZABLE)

        pygame.display.set_caption(f"Disegna & Anima Pro v{VERSION}")
        print(f"Schermo inizializzato: {self.w}x{self.h}")  # Log per debug

        self.clock = pygame.time.Clock()
        self.running = True

        # Fattore di scala per adattare UI a schermi diversi
        self.scale_factor = min(self.w, self.h) / 720.0
        self.scale_factor = max(0.8, min(1.5, self.scale_factor))

        self.state = "menu"
        self.menu_selection = 0

        self.project_name = "Senza titolo"
        self.canvas_w = 1280
        self.canvas_h = 720
        self.bg_color = C_WHITE
        self.fps = 12

        self.tool = "pen"
        self.color = C_BLACK
        self.brush_size = 4
        self.current_frame = 0
        self.frames = [[]]
        self.frame_stickmen = {}
        self.undo_stack = []
        self.is_playing = False
        self.play_index = 0
        self.play_timer = 0
        self.loop = True
        self.onion_skin = True
        self.grid_enabled = False
        self.snap_enabled = False
        self.theme_dark = False
        self.text_input = ""
        self.text_editing = False
        self.active_stickman = None
        self.detach_mode = False
        self.luffy_mode = False
        self.ragdoll_mode = False
        self.drawing = False
        self.start_pos = None
        self.current_points = []

        self.toolbar_scroll_x = 0
        self.toolbar_dragging = False
        self.toolbar_drag_start_x = 0
        self.toolbar_last_mouse_x = 0
        self.side_panel_open = False
        self.side_panel_x = self.w
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0

        self.canvas_surf = None
        self.canvas_dirty = True
        self.ui_dirty = True
        self.toolbar_surf = None
        self.tap_start_pos = None

        # Tastiera on-screen
        self.osk_active = False
        self.osk_buffer = ""
        self.osk_keys = []
        self.osk_text_target_pos = None

        # Menu Nuovo Progetto scrollabile
        self.np_scroll_y = 0
        self.np_max_scroll = 0
        self.np_drag_start_y = None
        self.np_scroll_start = 0

        # Nuove variabili per touch e viewport
        self.touch_down = False
        self.viewport_rect = pygame.Rect(0,0,0,0)
        self.pan_start_x = None
        self.pan_start_y = None
        self.pan_start_pan_x = 0
        self.pan_start_pan_y = 0

        # Rettangoli UI
        self.menu_rects = []
        self.menu_exit_rect = None
        self.np_field_rects = []
        self.np_color_rects = []
        self.np_back_rect = None
        self.np_ok_rect = None
        self.side_btn_rects = []
        self.timeline_btns = []
        self.color_rects = []
        self.tool_rects = []
        self.adv_btn_rect = None
        self.settings_back_rect = None

        self.newp_fields = [
            {"name": "Nome", "value": "Progetto1", "type": "text"},
            {"name": "Larghezza", "value": "1280", "type": "number"},
            {"name": "Altezza", "value": "720", "type": "number"},
            {"name": "FPS", "value": "12", "type": "number"},
        ]
        self.newp_selected_field = 0
        self.newp_colors = [C_WHITE, C_BLACK, (240,240,200), (200,230,255), (255,200,200)]
        self.newp_selected_color = 0

        self.toast_msg = ""
        self.toast_timer = 0

        self.build_ui()

    def show_toast(self, msg, duration=2000):
        self.toast_msg = msg
        self.toast_timer = duration

    def clamp_pan(self):
        """Limita pan_x e pan_y per non far uscire il canvas dall'area visibile."""
        z = self.base_zoom * self.zoom
        if z == 0:
            return
        canvas_disp_w = int(self.canvas_w * z)
        canvas_disp_h = int(self.canvas_h * z)
        avail_w = self.w - (self.side_panel_w if self.side_panel_open else 0)
        avail_h = self.h - self.top_h - self.toolbar_h - self.colorbar_h - self.timeline_h
        if canvas_disp_w <= avail_w:
            self.pan_x = 0
        else:
            min_pan_x = avail_w - canvas_disp_w
            max_pan_x = 0
            self.pan_x = max(min_pan_x, min(max_pan_x, self.pan_x))
        if canvas_disp_h <= avail_h:
            self.pan_y = 0
        else:
            min_pan_y = avail_h - canvas_disp_h
            max_pan_y = 0
            self.pan_y = max(min_pan_y, min(max_pan_y, self.pan_y))

    def update_canvas_rect(self):
        """Ricalcola solo canvas_rect senza ricostruire l'intera UI."""
        side_w = self.side_panel_w if self.side_panel_open else 0
        cw = self.w - side_w
        ch = self.h - self.top_h - self.toolbar_h - self.colorbar_h - self.timeline_h
        z = self.base_zoom * self.zoom
        if z < 0.1: z = 0.1
        cww = int(self.canvas_w * z)
        chh = int(self.canvas_h * z)
        self.clamp_pan()
        cx = (cw - cww) // 2 + self.pan_x
        cy = self.top_h + self.toolbar_h + self.colorbar_h + (ch - chh) // 2 + self.pan_y
        self.canvas_rect = pygame.Rect(cx, cy, cww, chh)
        self.viewport_rect = pygame.Rect(0, self.top_h + self.toolbar_h + self.colorbar_h,
                                         self.w, self.h - self.timeline_h - self.top_h - self.toolbar_h - self.colorbar_h)

    def build_ui(self):
        self.ui_dirty = True
        self.toolbar_items = [
            {"icon": "hand", "name": "Mano", "tool": "hand"},
            {"icon": "pen", "name": "Penna", "tool": "pen"},
            {"icon": "eraser", "name": "Gomma", "tool": "eraser"},
            {"icon": "line", "name": "Linea", "tool": "line"},
            {"icon": "circle", "name": "Cerchio", "tool": "circle"},
            {"icon": "rect", "name": "Rett.", "tool": "rect"},
            {"icon": "triangle", "name": "Triang.", "tool": "triangle"},
            {"icon": "star", "name": "Stella", "tool": "star"},
            {"icon": "fill", "name": "Fill", "tool": "fill"},
            {"icon": "text", "name": "Testo", "tool": "text"},
            {"icon": "stickman", "name": "Stick", "tool": "stickman"},
            {"icon": "zoom_in", "name": "Zoom+", "tool": "zoom_in"},
            {"icon": "zoom_out", "name": "Zoom-", "tool": "zoom_out"},
            {"icon": "grid", "name": "Griglia", "tool": "grid"},
            {"icon": "onion", "name": "Onion", "tool": "onion"},
            {"icon": "undo", "name": "Undo", "tool": "undo"},
            {"icon": "save", "name": "Salva", "tool": "save"},
            {"icon": "export", "name": "Exp", "tool": "export"},
        ]
        self.toolbar_item_w = int(95 * self.scale_factor)
        self.toolbar_item_h = int(80 * self.scale_factor)
        self.toolbar_gap = 10
        self.toolbar_total_w = len(self.toolbar_items) * (self.toolbar_item_w + self.toolbar_gap) + self.toolbar_gap

        self.top_h = int(65 * self.scale_factor)
        self.toolbar_h = int(95 * self.scale_factor)
        self.colorbar_h = int(70 * self.scale_factor)
        self.timeline_h = max(120, min(200, int(self.h * 0.15)))
        self.side_panel_w = min(int(360 * self.scale_factor), int(self.w * 0.4))

        side_w = self.side_panel_w if self.side_panel_open else 0
        cw = self.w - side_w
        ch = self.h - self.top_h - self.toolbar_h - self.colorbar_h - self.timeline_h
        if self.canvas_w > 0 and self.canvas_h > 0:
            self.base_zoom = min(cw / self.canvas_w, ch / self.canvas_h)
        else:
            self.base_zoom = 0.5
        if self.base_zoom < 0.2: self.base_zoom = 0.2
        z = self.base_zoom * self.zoom
        if z < 0.1: z = 0.1
        cww = int(self.canvas_w * z)
        chh = int(self.canvas_h * z)

        self.clamp_pan()

        cx = (cw - cww) // 2 + self.pan_x
        cy = self.top_h + self.toolbar_h + self.colorbar_h + (ch - chh) // 2 + self.pan_y
        self.canvas_rect = pygame.Rect(cx, cy, cww, chh)
        self.viewport_rect = pygame.Rect(0, self.top_h + self.toolbar_h + self.colorbar_h,
                                         self.w, self.h - self.timeline_h - self.top_h - self.toolbar_h - self.colorbar_h)

        if self.side_panel_open:
            self.side_panel_x = self.w - self.side_panel_w
        else:
            self.side_panel_x = self.w

    # ═══════════════════════════════════════════════════════════════
    #  MENU PRINCIPALE
    # ═══════════════════════════════════════════════════════════════
    def draw_menu(self):
        self.screen.fill(C_BG)
        fnt_big = get_font(int(72 * self.scale_factor))
        fnt = get_font(int(42 * self.scale_factor))
        fnt_small = get_font(int(24 * self.scale_factor))

        title = fnt_big.render("Disegna & Anima Pro", True, C_ACCENT)
        self.screen.blit(title, (self.w//2 - title.get_width()//2, self.h//8))

        ver = fnt_small.render(f"v{VERSION}", True, C_TEXT_DIM)
        self.screen.blit(ver, (self.w//2 - ver.get_width()//2, self.h//8 + 80))

        opts = ["Nuovo Progetto", "Carica Progetto", "Impostazioni"]
        bw = min(int(700 * self.scale_factor), self.w - 40)
        bh = int(110 * self.scale_factor)
        by = self.h//3
        self.menu_rects = []
        for i, txt in enumerate(opts):
            col = C_ACCENT if i == self.menu_selection else C_PANEL_L
            rect = pygame.Rect(self.w//2 - bw//2, by + i*(bh+25), bw, bh)
            pygame.draw.rect(self.screen, col, rect, border_radius=18)
            if i == self.menu_selection:
                pygame.draw.rect(self.screen, C_WHITE, rect, 3, border_radius=18)
            t = fnt.render(txt, True, C_WHITE)
            self.screen.blit(t, (rect.centerx - t.get_width()//2, rect.centery - t.get_height()//2))
            self.menu_rects.append((rect, i))

        exit_rect = pygame.Rect(self.w//2 - 120, self.h - 100, 240, 70)
        pygame.draw.rect(self.screen, C_RED, exit_rect, border_radius=15)
        t_exit = fnt.render("Esci", True, C_WHITE)
        self.screen.blit(t_exit, (exit_rect.centerx - t_exit.get_width()//2, exit_rect.centery - t_exit.get_height()//2))
        self.menu_exit_rect = exit_rect
        pygame.display.flip()

    def handle_menu_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False; return
            if event.type == pygame.VIDEORESIZE:
                self.w, self.h = event.size
                self.screen = pygame.display.set_mode((self.w, self.h), pygame.RESIZABLE)
                self.scale_factor = min(self.w, self.h) / 720.0
                self.scale_factor = max(0.8, min(1.5, self.scale_factor))
                self.build_ui()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button != 1: continue
                pos = event.pos
                for rect, idx in self.menu_rects:
                    if rect.collidepoint(pos):
                        self.menu_selection = idx
                        if idx == 0:
                            self.state = "new_project"; self.build_ui()
                        elif idx == 1:
                            self.load_project_dialog()
                        elif idx == 2:
                            self.state = "settings_menu"; self.build_ui()
                        return
                if hasattr(self, 'menu_exit_rect') and self.menu_exit_rect.collidepoint(pos):
                    self.running = False
                    return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP: self.menu_selection = (self.menu_selection - 1) % 3
                if event.key == pygame.K_DOWN: self.menu_selection = (self.menu_selection + 1) % 3
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    if self.menu_selection == 0: self.state = "new_project"; self.build_ui()
                    elif self.menu_selection == 1: self.load_project_dialog()
                    elif self.menu_selection == 2: self.state = "settings_menu"; self.build_ui()

    def load_project_dialog(self):
        try:
            files = [f for f in os.listdir(APP_DIR) if f.endswith(".json")]
            if files:
                files.sort(key=lambda x: os.path.getmtime(os.path.join(APP_DIR, x)), reverse=True)
                self.load_project(files[0])
                self.state = "editor"
                self.build_ui()
                self.show_toast(f"Caricato: {files[0]}")
            else:
                self.show_toast("Nessun progetto trovato")
        except Exception as e:
            self.show_toast(f"Errore: {str(e)}")

    # ═══════════════════════════════════════════════════════════════
    #  IMPOSTAZIONI
    # ═══════════════════════════════════════════════════════════════
    def draw_settings_menu(self):
        self.screen.fill(C_BG)
        fnt_big = get_font(int(52 * self.scale_factor))
        fnt = get_font(int(28 * self.scale_factor))
        title = fnt_big.render("Impostazioni", True, C_ACCENT)
        self.screen.blit(title, (self.w//2 - title.get_width()//2, 60))
        info_lines = [
            f"Versione: {VERSION}",
            "",
            "App ottimizzata per Android / Pydroid",
            "Tutti i controlli sono touch.",
            "",
            "Disegna, anima stickman",
            "e esporta in PNG/GIF.",
        ]
        y = 160
        for line in info_lines:
            t = fnt.render(line, True, C_TEXT_DIM)
            self.screen.blit(t, (self.w//2 - t.get_width()//2, y))
            y += 45

        back_rect = pygame.Rect(self.w//2 - 130, self.h - 130, 260, 80)
        pygame.draw.rect(self.screen, C_PANEL_L, back_rect, border_radius=14)
        pygame.draw.rect(self.screen, C_WHITE, back_rect, 3, border_radius=14)
        t = fnt.render("Indietro", True, C_WHITE)
        self.screen.blit(t, (back_rect.centerx - t.get_width()//2, back_rect.centery - t.get_height()//2))
        self.settings_back_rect = back_rect
        pygame.display.flip()

    def handle_settings_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False; return
            if event.type == pygame.VIDEORESIZE:
                self.w, self.h = event.size
                self.screen = pygame.display.set_mode((self.w, self.h), pygame.RESIZABLE)
                self.scale_factor = min(self.w, self.h) / 720.0
                self.scale_factor = max(0.8, min(1.5, self.scale_factor))
                self.build_ui()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button != 1: continue
                pos = event.pos
                if hasattr(self, 'settings_back_rect') and self.settings_back_rect.collidepoint(pos):
                    self.state = "menu"; self.build_ui(); return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = "menu"; self.build_ui()

    # ═══════════════════════════════════════════════════════════════
    #  NUOVO PROGETTO (scrollabile)
    # ═══════════════════════════════════════════════════════════════
    def draw_new_project(self):
        self.screen.fill(C_BG)
        fnt_big = get_font(int(50 * self.scale_factor))
        fnt = get_font(int(32 * self.scale_factor))
        fnt_small = get_font(int(22 * self.scale_factor))

        off_y = -self.np_scroll_y

        title = fnt_big.render("Nuovo Progetto", True, C_ACCENT)
        self.screen.blit(title, (self.w//2 - title.get_width()//2, 40 + off_y))

        fh = int(85 * self.scale_factor)
        fw = min(int(650 * self.scale_factor), self.w - 40)
        fy = 130 + off_y
        self.np_field_rects = []
        for i, field in enumerate(self.newp_fields):
            rect = pygame.Rect(self.w//2 - fw//2, fy + i*(fh+20), fw, fh)
            sel = (i == self.newp_selected_field)
            col = C_ACCENT if sel else C_PANEL_L
            pygame.draw.rect(self.screen, col, rect, border_radius=12)
            if sel: pygame.draw.rect(self.screen, C_WHITE, rect, 3, border_radius=12)
            label = fnt_small.render(field["name"], True, C_TEXT_DIM)
            self.screen.blit(label, (rect.x + 20, rect.y + 10))
            val = fnt.render(field["value"], True, C_WHITE)
            self.screen.blit(val, (rect.x + 20, rect.y + 45))
            self.np_field_rects.append(rect)

        cy = fy + len(self.newp_fields)*(fh+20) + 30
        cr = int(40 * self.scale_factor)
        cx = self.w//2 - len(self.newp_colors)*(cr*2+20)//2
        self.np_color_rects = []
        for i, c in enumerate(self.newp_colors):
            rect = pygame.Rect(cx + i*(cr*2+20), cy, cr*2, cr*2)
            pygame.draw.ellipse(self.screen, c, rect)
            if i == self.newp_selected_color:
                pygame.draw.ellipse(self.screen, C_ACCENT, rect, 4)
            self.np_color_rects.append(rect)

        margin = 20
        bw = (self.w - margin*3) // 2
        bh = int(70 * self.scale_factor)
        by = self.h - bh - margin
        back_r = pygame.Rect(margin, by, bw, bh)
        ok_r = pygame.Rect(margin*2 + bw, by, bw, bh)
        pygame.draw.rect(self.screen, C_PANEL_L, back_r, border_radius=14)
        pygame.draw.rect(self.screen, C_GREEN, ok_r, border_radius=14)
        t1 = fnt.render("Indietro", True, C_WHITE)
        t2 = fnt.render("Crea!", True, C_WHITE)
        self.screen.blit(t1, (back_r.centerx - t1.get_width()//2, back_r.centery - t1.get_height()//2))
        self.screen.blit(t2, (ok_r.centerx - t2.get_width()//2, ok_r.centery - t2.get_height()//2))
        self.np_back_rect = back_r
        self.np_ok_rect = ok_r

        fixed_bottom = bh + margin*3
        last_scrollable_y = cy + cr*2 + 40
        self.np_max_scroll = max(0, last_scrollable_y - (self.h - fixed_bottom))
        if self.np_scroll_y < -self.np_max_scroll:
            self.np_scroll_y = -self.np_max_scroll
        if self.np_scroll_y > 0:
            self.np_scroll_y = 0

        pygame.display.flip()

    def handle_new_project_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False; return
            if event.type == pygame.VIDEORESIZE:
                self.w, self.h = event.size
                self.screen = pygame.display.set_mode((self.w, self.h), pygame.RESIZABLE)
                self.scale_factor = min(self.w, self.h) / 720.0
                self.scale_factor = max(0.8, min(1.5, self.scale_factor))
                self.build_ui()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button != 1: continue
                pos = event.pos
                if self.np_back_rect.collidepoint(pos):
                    self.state = "menu"; self.build_ui(); return
                if self.np_ok_rect.collidepoint(pos):
                    self.create_project(); return
                for i, rect in enumerate(self.np_field_rects):
                    if rect.collidepoint(pos):
                        self.newp_selected_field = i; return
                for i, rect in enumerate(self.np_color_rects):
                    if rect.collidepoint(pos):
                        self.newp_selected_color = i; return
                self.np_drag_start_y = pos[1]
                self.np_scroll_start = self.np_scroll_y
            if event.type == pygame.MOUSEMOTION:
                if self.np_drag_start_y is not None:
                    dy = event.pos[1] - self.np_drag_start_y
                    self.np_scroll_y = self.np_scroll_start - dy
                    self.np_scroll_y = max(-self.np_max_scroll, min(0, self.np_scroll_y))
            if event.type == pygame.MOUSEBUTTONUP:
                self.np_drag_start_y = None
            if event.type == pygame.KEYDOWN:
                field = self.newp_fields[self.newp_selected_field]
                if event.key == pygame.K_BACKSPACE:
                    field["value"] = field["value"][:-1]
                elif event.key == pygame.K_TAB or event.key == pygame.K_DOWN:
                    self.newp_selected_field = (self.newp_selected_field + 1) % len(self.newp_fields)
                elif event.key == pygame.K_UP:
                    self.newp_selected_field = (self.newp_selected_field - 1) % len(self.newp_fields)
                elif event.unicode.isprintable():
                    if field["type"] == "number" and event.unicode.isdigit():
                        field["value"] += event.unicode
                    elif field["type"] == "text":
                        field["value"] += event.unicode

    def create_project(self):
        try:
            self.project_name = self.newp_fields[0]["value"] or "Senza titolo"
            w = int(self.newp_fields[1]["value"])
            h_val = int(self.newp_fields[2]["value"])
            fps = int(self.newp_fields[3]["value"])
            if w < 100 or w > 4000 or h_val < 100 or h_val > 4000 or fps < 1 or fps > 60:
                self.show_toast("Valori non validi (100-4000, 1-60fps)")
                return
            self.canvas_w = w
            self.canvas_h = h_val
            self.fps = fps
            self.bg_color = self.newp_colors[self.newp_selected_color]
            self.frames = [[]]
            self.frame_stickmen = {}
            self.current_frame = 0
            self.state = "editor"
            self.build_ui()
            self.canvas_dirty = True
        except ValueError:
            self.show_toast("Inserisci numeri validi!")

    # ═══════════════════════════════════════════════════════════════
    #  EDITOR
    # ═══════════════════════════════════════════════════════════════
    def draw_editor(self):
        bg = C_BG if self.theme_dark else (220,220,225)
        self.screen.fill(bg)

        # Top bar
        pygame.draw.rect(self.screen, C_PANEL, (0, 0, self.w, self.top_h))
        fnt = get_font(int(22 * self.scale_factor))
        title = fnt.render(f"{self.project_name}  |  Frame {self.current_frame+1}/{len(self.frames)}  |  {self.tool.upper()}", True, C_TEXT)
        self.screen.blit(title, (15, self.top_h//2 - title.get_height()//2))

        menu_r = pygame.Rect(self.w - 60, 8, 45, 45)
        pygame.draw.rect(self.screen, C_PANEL_L, menu_r, border_radius=10)
        ICONS["menu"](self.screen, menu_r, C_WHITE)
        self.menu_btn_rect = menu_r

        adv_r = pygame.Rect(self.w - 115, 8, 45, 45)
        pygame.draw.rect(self.screen, C_ACCENT if self.side_panel_open else C_PANEL_L, adv_r, border_radius=10)
        ICONS["settings"](self.screen, adv_r, C_WHITE)
        self.adv_btn_rect = adv_r

        # Toolbar
        toolbar_y = self.top_h
        pygame.draw.rect(self.screen, C_PANEL, (0, toolbar_y, self.w, self.toolbar_h))

        if self.toolbar_surf is None or self.ui_dirty:
            self.toolbar_surf = pygame.Surface((self.toolbar_total_w, self.toolbar_h), pygame.SRCALPHA)
            self.toolbar_surf.fill((0,0,0,0))
            for i, item in enumerate(self.toolbar_items):
                x = self.toolbar_gap + i * (self.toolbar_item_w + self.toolbar_gap)
                rect = pygame.Rect(x, 4, self.toolbar_item_w, self.toolbar_h - 8)
                active = (self.tool == item["tool"])
                col = C_ACCENT if active else (C_PANEL_L if i%2==0 else C_PANEL)
                pygame.draw.rect(self.toolbar_surf, col, rect, border_radius=10)
                if active:
                    pygame.draw.rect(self.toolbar_surf, C_WHITE, rect, 3, border_radius=10)
                ir = rect.copy(); ir.height = 34; ir.width = 34; ir.center = rect.center
                ir.centery -= 6
                ICONS[item["icon"]](self.toolbar_surf, ir, C_WHITE)
                nf = get_font(int(14 * self.scale_factor))
                t = nf.render(item["name"], True, C_TEXT_DIM)
                self.toolbar_surf.blit(t, (rect.centerx - t.get_width()//2, rect.bottom - 16))
            self.ui_dirty = False

        visible_w = self.w - (self.side_panel_w if self.side_panel_open else 0)
        self.screen.blit(self.toolbar_surf, (self.toolbar_scroll_x, toolbar_y), (0, 0, visible_w, self.toolbar_h))

        # Color bar
        colorbar_y = toolbar_y + self.toolbar_h
        pygame.draw.rect(self.screen, C_PANEL, (0, colorbar_y, visible_w, self.colorbar_h))
        cr = int(28 * self.scale_factor)
        cx = 20
        self.color_rects = []
        for c in COLORS:
            rect = pygame.Rect(cx, colorbar_y + (self.colorbar_h - cr*2)//2, cr*2, cr*2)
            pygame.draw.ellipse(self.screen, c, rect)
            if self.color == c:
                pygame.draw.ellipse(self.screen, C_ACCENT, rect, 4)
            self.color_rects.append((rect, c))
            cx += cr*2 + 24

        # Canvas
        self.draw_canvas()
        if self.drawing and self.current_points:
            self.draw_preview()

        # Side panel
        self.side_panel_x = self.w - self.side_panel_w if self.side_panel_open else self.w
        if self.side_panel_open:
            self.draw_side_panel()

        # Timeline
        self.draw_timeline()

        # Tastiera on-screen
        if self.osk_active:
            self.draw_osk()

        # Toast
        if self.toast_timer > 0:
            self.toast_timer -= self.clock.get_time()
            tf = get_font(int(24 * self.scale_factor))
            ts = tf.render(self.toast_msg, True, C_WHITE)
            tr = ts.get_rect(center=(self.w//2, self.h - self.timeline_h - 40))
            pad = 15
            pygame.draw.rect(self.screen, (40,40,50), (tr.x-pad, tr.y-pad, tr.w+pad*2, tr.h+pad*2), border_radius=10)
            self.screen.blit(ts, tr)

        pygame.display.flip()

    def draw_preview(self):
        if not self.current_points:
            return
        z = self.base_zoom * self.zoom
        if z == 0:
            return
        screen_points = []
        for lp in self.current_points:
            sx = self.canvas_rect.x + int(lp[0] * z)
            sy = self.canvas_rect.y + int(lp[1] * z)
            screen_points.append((sx, sy))
        if self.tool in ("pen", "eraser"):
            col = self.bg_color if self.tool == "eraser" else self.color
            sz = max(1, int(self.brush_size * z * (3 if self.tool == "eraser" else 1)))
            if len(screen_points) > 1:
                pygame.draw.lines(self.screen, col, False, screen_points, sz)
        elif self.tool in ("line", "circle", "rect", "triangle", "star"):
            if len(screen_points) > 0 and self.start_pos:
                start_screen = (self.canvas_rect.x + int(self.start_pos[0] * z),
                                self.canvas_rect.y + int(self.start_pos[1] * z))
                end_screen = screen_points[-1]
                pts = self.build_shape(self.tool, [self.start_pos[0], self.start_pos[1]], 
                                       [self.current_points[-1][0], self.current_points[-1][1]])
                screen_pts = []
                for p in pts:
                    sx = self.canvas_rect.x + int(p[0] * z)
                    sy = self.canvas_rect.y + int(p[1] * z)
                    screen_pts.append((sx, sy))
                if len(screen_pts) > 1:
                    pygame.draw.lines(self.screen, C_ACCENT, False, screen_pts, max(1, int(self.brush_size * z)))

    def draw_side_panel(self):
        x = self.side_panel_x
        w = self.side_panel_w
        h_panel = self.h - self.top_h - self.timeline_h
        pygame.draw.rect(self.screen, C_PANEL, (x, self.top_h, w, h_panel))
        pygame.draw.line(self.screen, (50,50,60), (x, self.top_h), (x, self.h - self.timeline_h), 2)

        fnt = get_font(int(22 * self.scale_factor))
        fnt_small = get_font(int(16 * self.scale_factor))
        y = self.top_h + 10

        t = fnt.render("Avanzate", True, C_ACCENT)
        self.screen.blit(t, (x + 15, y)); y += 28

        t = fnt.render("Stickman", True, C_TEXT)
        self.screen.blit(t, (x + 15, y)); y += 26

        self.side_btn_rects = []
        half_w = (w - 40) // 2
        btn_h = max(60, int(45 * self.scale_factor))

        rect = pygame.Rect(x + 15, y, w - 30, btn_h)
        pygame.draw.rect(self.screen, C_GREEN, rect, border_radius=10)
        ir = pygame.Rect(0, 0, 24, 24); ir.center = (rect.x + 25, rect.centery)
        ICONS["add"](self.screen, ir, C_WHITE)
        t2 = fnt_small.render("Aggiungi", True, C_WHITE)
        self.screen.blit(t2, (rect.x + 50, rect.centery - t2.get_height()//2))
        self.side_btn_rects.append((rect, self.spawn_stickman))
        y += btn_h + 6

        r1 = pygame.Rect(x + 15, y, half_w, btn_h)
        r2 = pygame.Rect(x + 15 + half_w + 10, y, half_w, btn_h)
        for r, ic, txt, act in [(r1, "resize_up", "Grande", self.grow_stickman), (r2, "resize_down", "Piccolo", self.shrink_stickman)]:
            pygame.draw.rect(self.screen, C_PANEL_L, r, border_radius=10)
            ir = pygame.Rect(0, 0, 22, 22); ir.center = (r.x + 20, r.centery)
            ICONS[ic](self.screen, ir, C_WHITE)
            t2 = fnt_small.render(txt, True, C_WHITE)
            self.screen.blit(t2, (r.x + 38, r.centery - t2.get_height()//2))
            self.side_btn_rects.append((r, act))
        y += btn_h + 6

        r1 = pygame.Rect(x + 15, y, half_w, btn_h)
        r2 = pygame.Rect(x + 15 + half_w + 10, y, half_w, btn_h)
        for r, ic, txt, act in [(r1, "reset", "Reset", self.reset_stickman_pose), (r2, "settings", "Tema", self.toggle_theme)]:
            pygame.draw.rect(self.screen, C_PANEL_L, r, border_radius=10)
            ir = pygame.Rect(0, 0, 22, 22); ir.center = (r.x + 20, r.centery)
            ICONS[ic](self.screen, ir, C_WHITE)
            t2 = fnt_small.render(txt, True, C_WHITE)
            self.screen.blit(t2, (r.x + 38, r.centery - t2.get_height()//2))
            self.side_btn_rects.append((r, act))
        y += btn_h + 6

        r1 = pygame.Rect(x + 15, y, half_w, btn_h)
        r2 = pygame.Rect(x + 15 + half_w + 10, y, half_w, btn_h)
        for r, txt, act in [(r1, "Size+", self.inc_brush), (r2, "Size-", self.dec_brush)]:
            pygame.draw.rect(self.screen, C_PANEL_L, r, border_radius=10)
            t2 = fnt_small.render(txt, True, C_WHITE)
            self.screen.blit(t2, (r.centerx - t2.get_width()//2, r.centery - t2.get_height()//2))
            self.side_btn_rects.append((r, act))
        y += btn_h + 6

        rect = pygame.Rect(x + 15, y, w - 30, btn_h)
        pygame.draw.rect(self.screen, C_RED, rect, border_radius=10)
        t2 = fnt_small.render("Pulisci Canvas", True, C_WHITE)
        self.screen.blit(t2, (rect.centerx - t2.get_width()//2, rect.centery - t2.get_height()//2))
        self.side_btn_rects.append((rect, self.clear_canvas))
        y += btn_h + 12

        t2 = fnt_small.render(f"Spessore: {self.brush_size}", True, C_TEXT_DIM)
        self.screen.blit(t2, (x + 15, y)); y += 22

        t = fnt.render("Mod", True, C_TEXT)
        self.screen.blit(t, (x + 15, y)); y += 26

        r1 = pygame.Rect(x + 15, y, half_w, btn_h)
        r2 = pygame.Rect(x + 15 + half_w + 10, y, half_w, btn_h)
        for r, (txt, ic, active, act) in zip([r1, r2], [
            ("Luffy", "luffy", self.luffy_mode, self.toggle_luffy),
            ("Ragdoll", "ragdoll", self.ragdoll_mode, self.toggle_ragdoll)]):
            col = C_ACCENT if active else C_PANEL_L
            pygame.draw.rect(self.screen, col, r, border_radius=10)
            ir = pygame.Rect(0, 0, 22, 22); ir.center = (r.x + 20, r.centery)
            ICONS[ic](self.screen, ir, C_WHITE)
            t2 = fnt_small.render(txt + (" ON" if active else ""), True, C_WHITE)
            self.screen.blit(t2, (r.x + 38, r.centery - t2.get_height()//2))
            self.side_btn_rects.append((r, act))
        y += btn_h + 6

        rect = pygame.Rect(x + 15, y, w - 30, btn_h)
        col = C_ACCENT if self.detach_mode else C_PANEL_L
        pygame.draw.rect(self.screen, col, rect, border_radius=10)
        ir = pygame.Rect(0, 0, 22, 22); ir.center = (rect.x + 25, rect.centery)
        ICONS["detach"](self.screen, ir, C_WHITE)
        t2 = fnt_small.render("Stacca Arto" + (" ON" if self.detach_mode else ""), True, C_WHITE)
        self.screen.blit(t2, (rect.x + 50, rect.centery - t2.get_height()//2))
        self.side_btn_rects.append((rect, self.toggle_detach))

    def draw_timeline(self):
        ty = self.h - self.timeline_h
        pygame.draw.rect(self.screen, C_PANEL, (0, ty, self.w, self.timeline_h))

        bw = int(100 * self.scale_factor)
        bh = int(75 * self.scale_factor)
        gap = 12
        tx = 20; tcy = ty + self.timeline_h//2
        self.timeline_btns = []
        for ic, act in [("arrow_left", self.prev_frame), ("play" if not self.is_playing else "pause", self.toggle_play), ("arrow_right", self.next_frame)]:
            rect = pygame.Rect(tx, tcy - bh//2, bw, bh)
            pygame.draw.rect(self.screen, C_PANEL_L, rect, border_radius=12)
            ICONS[ic](self.screen, rect, C_WHITE)
            self.timeline_btns.append((rect, act))
            tx += bw + gap

        fnt = get_font(int(22 * self.scale_factor))
        info = fnt.render(f"{self.current_frame+1} / {len(self.frames)}", True, C_TEXT)
        self.screen.blit(info, (tx + 12, tcy - info.get_height()//2))
        tx += 100

        for txt, act, bg in [("+F", self.add_frame, None), ("Dup", self.dup_frame, None), ("Del", self.del_frame, C_RED)]:
            rect = pygame.Rect(tx, tcy - bh//2, bw, bh)
            col = bg if bg else C_PANEL_L
            pygame.draw.rect(self.screen, col, rect, border_radius=12)
            t = fnt.render(txt, True, C_WHITE)
            self.screen.blit(t, (rect.centerx - t.get_width()//2, rect.centery - t.get_height()//2))
            self.timeline_btns.append((rect, act))
            tx += bw + gap

        thumb_w = max(int(75 * self.scale_factor), int(self.w * 0.09))
        thumb_h = max(int(55 * self.scale_factor), int(self.timeline_h * 0.45))
        max_visible = max(1, (self.w - tx - 20) // (thumb_w + 8))
        start_idx = max(0, min(self.current_frame - max_visible//2, len(self.frames) - max_visible))
        end_idx = min(len(self.frames), start_idx + max_visible)
        start_x = self.w - (end_idx - start_idx) * (thumb_w + 8) - 10
        if start_x < tx + 20:
            start_x = tx + 20
        tyy = ty + self.timeline_h - thumb_h - 15
        for i in range(start_idx, end_idx):
            rect = pygame.Rect(start_x + (i - start_idx)*(thumb_w+8), tyy, thumb_w, thumb_h)
            active = (i == self.current_frame and not self.is_playing)
            has = len(self.frames[i]) > 0 or i in self.frame_stickmen
            col = C_ACCENT if active else (C_PANEL_L if has else (40,40,50))
            pygame.draw.rect(self.screen, col, rect, border_radius=8)
            border = C_WHITE if active else (C_ACCENT if has else (50,50,60))
            pygame.draw.rect(self.screen, border, rect, 3 if active else 1, border_radius=8)
            t = fnt.render(str(i+1), True, C_WHITE)
            self.screen.blit(t, (rect.centerx - t.get_width()//2, rect.centery - t.get_height()//2))

    def draw_canvas(self):
        if self.canvas_surf is None or self.canvas_surf.get_size() != (self.canvas_w, self.canvas_h):
            self.canvas_surf = pygame.Surface((self.canvas_w, self.canvas_h))
            self.canvas_dirty = True

        if self.canvas_dirty:
            self.canvas_surf.fill(self.bg_color)

            # Onion skin
            if self.onion_skin and self.current_frame > 0 and not self.is_playing:
                prev = self.current_frame - 1
                if prev >= 0 and prev < len(self.frames):
                    for stroke in self.frames[prev]:
                        pts = stroke.get("points", [])
                        if len(pts) > 1:
                            pygame.draw.lines(self.canvas_surf, C_ONION, False, pts, max(1, stroke.get("size", 2)//2))

            target = self.play_index if self.is_playing else self.current_frame
            if 0 <= target < len(self.frames):
                for stroke in self.frames[target]:
                    pts = stroke.get("points", [])
                    if len(pts) > 1:
                        col = self.bg_color if stroke.get("is_eraser") else stroke.get("color", C_BLACK)
                        pygame.draw.lines(self.canvas_surf, col, False, pts, stroke.get("size", 2))
                    elif stroke.get("tool") == "text" and len(pts) == 1:
                        txt = stroke.get("text", "")
                        if txt:
                            fnt = get_font(max(12, stroke.get("size", 2) * 3))
                            ts = fnt.render(txt, True, stroke.get("color", C_BLACK))
                            self.canvas_surf.blit(ts, (int(pts[0][0]), int(pts[0][1])))

                if target in self.frame_stickmen:
                    for sm in self.frame_stickmen[target]:
                        is_active = (sm == self.active_stickman)
                        sm.draw(self.canvas_surf,
                                C_BLACK if not self.theme_dark else C_WHITE,
                                show_joints=(is_active and self.tool == "hand"),
                                is_selected=is_active,
                                luffy_mode=self.luffy_mode,
                                theme_dark=self.theme_dark)

            if self.grid_enabled:
                g = 40
                gc = (180,180,190) if self.theme_dark else (200,200,210)
                for x in range(0, self.canvas_w, g):
                    pygame.draw.line(self.canvas_surf, gc, (x, 0), (x, self.canvas_h), 1)
                for y in range(0, self.canvas_h, g):
                    pygame.draw.line(self.canvas_surf, gc, (0, y), (self.canvas_w, y), 1)

            self.canvas_dirty = False

        z = self.base_zoom * self.zoom
        if z > 0:
            try:
                scaled = pygame.transform.scale(self.canvas_surf, (int(self.canvas_w * z), int(self.canvas_h * z)))
                visible_rect = self.canvas_rect.clip(self.viewport_rect)
                if visible_rect.width > 0 and visible_rect.height > 0:
                    src_x = visible_rect.x - self.canvas_rect.x
                    src_y = visible_rect.y - self.canvas_rect.y
                    self.screen.blit(scaled, (visible_rect.x, visible_rect.y),
                                     area=(src_x, src_y, visible_rect.width, visible_rect.height))
                pygame.draw.rect(self.screen, C_ACCENT, self.viewport_rect, 2)
            except:
                pass

    def draw_osk(self):
        kb_h = min(320, int(self.h * 0.28))
        kb_y = self.h - kb_h
        pygame.draw.rect(self.screen, C_PANEL, (0, kb_y, self.w, kb_h))

        if self.osk_text_target_pos:
            z = self.base_zoom * self.zoom
            if z > 0:
                sx = self.canvas_rect.x + int(self.osk_text_target_pos[0] * z)
                sy = self.canvas_rect.y + int(self.osk_text_target_pos[1] * z)
                fnt_prev = get_font(int(28 * self.scale_factor))
                prev_surf = fnt_prev.render(self.osk_buffer + "|", True, C_WHITE)
                pad = 8
                bg_rect = pygame.Rect(sx - pad, sy - prev_surf.get_height() - pad,
                                      prev_surf.get_width() + pad*2, prev_surf.get_height() + pad*2)
                pygame.draw.rect(self.screen, (50,50,60), bg_rect, border_radius=8)
                self.screen.blit(prev_surf, (sx, sy - prev_surf.get_height()))
            else:
                fnt_prev = get_font(int(28 * self.scale_factor))
                prev_surf = fnt_prev.render(self.osk_buffer + "|", True, C_WHITE)
                self.screen.blit(prev_surf, (20, 20))

        rows = ["1234567890", "QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
        key_w = max(55, min(int(80 * self.scale_factor), int(self.w / 12)))
        key_h = max(65, int(60 * self.scale_factor))
        gap = 8
        self.osk_keys = []
        start_y = kb_y + 20
        for ri, row in enumerate(rows):
            total_w = len(row) * key_w + (len(row)-1) * gap
            start_x = (self.w - total_w) // 2
            for ci, ch in enumerate(row):
                rect = pygame.Rect(start_x + ci*(key_w+gap), start_y + ri*(key_h+gap), key_w, key_h)
                pygame.draw.rect(self.screen, C_PANEL_L, rect, border_radius=8)
                t = get_font(int(24 * self.scale_factor)).render(ch, True, C_WHITE)
                self.screen.blit(t, (rect.centerx - t.get_width()//2, rect.centery - t.get_height()//2))
                self.osk_keys.append((rect, ch, "char"))

        sp_y = start_y + len(rows)*(key_h+gap) + 10
        sp_w = max(80, int(120 * self.scale_factor))
        specials = [("Spazio", "space"), ("Canc", "back"), ("Invio", "enter"), ("Annulla", "cancel")]
        total_sp = len(specials) * sp_w + (len(specials)-1) * gap
        start_x = (self.w - total_sp) // 2
        for i, (label, action) in enumerate(specials):
            rect = pygame.Rect(start_x + i*(sp_w+gap), sp_y, sp_w, key_h)
            col = C_ACCENT2 if action == "enter" else (C_RED if action == "cancel" else C_PANEL_L)
            pygame.draw.rect(self.screen, col, rect, border_radius=8)
            t = get_font(int(20 * self.scale_factor)).render(label, True, C_WHITE)
            self.screen.blit(t, (rect.centerx - t.get_width()//2, rect.centery - t.get_height()//2))
            self.osk_keys.append((rect, label, action))

    def handle_editor_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False; return
            if event.type == pygame.VIDEORESIZE:
                self.w, self.h = event.size
                self.screen = pygame.display.set_mode((self.w, self.h), pygame.RESIZABLE)
                self.scale_factor = min(self.w, self.h) / 720.0
                self.scale_factor = max(0.8, min(1.5, self.scale_factor))
                self.build_ui()

            # Gestione pausa/ripresa Android
            if event.type == pygame.APP_WILLENTERBACKGROUND:
                self.is_playing = False
                self.drawing = False
                self.toolbar_dragging = False
                print("App in background")
            elif event.type == pygame.APP_DIDENTERFOREGROUND:
                self.canvas_dirty = True
                print("App in foreground")

            if self.osk_active:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for rect, val, action in self.osk_keys:
                        if rect.collidepoint(event.pos):
                            if action == "char":
                                self.osk_buffer += val
                            elif action == "space":
                                self.osk_buffer += " "
                            elif action == "back":
                                self.osk_buffer = self.osk_buffer[:-1]
                            elif action == "enter":
                                if self.osk_buffer.strip():
                                    self.frames[self.current_frame].append({
                                        "points": [self.osk_text_target_pos],
                                        "color": self.color,
                                        "size": self.brush_size,
                                        "is_eraser": False,
                                        "tool": "text",
                                        "text": self.osk_buffer})
                                    self.canvas_dirty = True
                                self.osk_active = False
                                self.osk_buffer = ""
                                self.osk_text_target_pos = None
                            elif action == "cancel":
                                self.osk_active = False
                                self.osk_buffer = ""
                                self.osk_text_target_pos = None
                            return
                continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self._mouse_down(event)
            elif event.type == pygame.MOUSEMOTION:
                self._mouse_move(event)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self._mouse_up(event)
            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0: self.zoom_in()
                elif event.y < 0: self.zoom_out()

            if event.type == pygame.KEYDOWN and not self.osk_active:
                if self.text_editing:
                    if event.key == pygame.K_RETURN:
                        self.text_editing = False
                        if self.text_input.strip():
                            self.frames[self.current_frame].append({
                                "points": [self.start_pos], "color": self.color, "size": self.brush_size,
                                "is_eraser": False, "tool": "text", "text": self.text_input})
                            self.canvas_dirty = True
                        self.text_input = ""
                    elif event.key == pygame.K_BACKSPACE:
                        self.text_input = self.text_input[:-1]
                    else:
                        self.text_input += event.unicode
                else:
                    if event.key == pygame.K_SPACE: self.toggle_play()
                    elif event.key == pygame.K_z and (pygame.key.get_mods() & pygame.KMOD_CTRL): self.undo()
                    elif event.key == pygame.K_LEFT: self.prev_frame()
                    elif event.key == pygame.K_RIGHT: self.next_frame()

    def _mouse_down(self, event):
        if event.button != 1: return
        pos = event.pos
        self.tap_start_pos = pos
        self.touch_down = True

        if hasattr(self, 'menu_btn_rect') and self.menu_btn_rect and self.menu_btn_rect.collidepoint(pos):
            self.save_project(); return

        if hasattr(self, 'adv_btn_rect') and self.adv_btn_rect and self.adv_btn_rect.collidepoint(pos):
            self.side_panel_open = not self.side_panel_open
            self.build_ui(); return

        toolbar_y = self.top_h
        if 0 <= pos[0] <= self.w - (self.side_panel_w if self.side_panel_open else 0) and toolbar_y <= pos[1] <= toolbar_y + self.toolbar_h:
            self.toolbar_dragging = True
            self.toolbar_last_mouse_x = pos[0]
            for i, item in enumerate(self.toolbar_items):
                ix = self.toolbar_gap + i * (self.toolbar_item_w + self.toolbar_gap) + self.toolbar_scroll_x
                if ix <= pos[0] <= ix + self.toolbar_item_w and toolbar_y + 2 <= pos[1] <= toolbar_y + self.toolbar_h - 2:
                    t = item["tool"]
                    if t == "zoom_in": self.zoom_in(); return
                    if t == "zoom_out": self.zoom_out(); return
                    if t == "grid": self.toggle_grid(); return
                    if t == "onion": self.toggle_onion(); return
                    if t == "undo": self.undo(); return
                    if t == "save": self.save_project(); return
                    if t == "export": self.export_png(); return
                    self.set_tool(t)
                    return
            return

        colorbar_y = toolbar_y + self.toolbar_h
        if 0 <= pos[0] <= self.w - (self.side_panel_w if self.side_panel_open else 0) and colorbar_y <= pos[1] <= colorbar_y + self.colorbar_h:
            for rect, c in self.color_rects:
                if rect.collidepoint(pos):
                    self.color = c; return

        if self.side_panel_open and pos[0] >= self.side_panel_x:
            self._handle_side_panel_click(pos)
            return

        ty = self.h - self.timeline_h
        if pos[1] >= ty:
            self._handle_timeline_click(pos)
            return

        if self.canvas_rect.collidepoint(pos):
            lp = self.to_local(pos)
            lp = self.snap_pos(lp)

            if self.tool == "hand":
                sms = self.frame_stickmen.get(self.current_frame, [])
                hit = False
                for sm in reversed(sms):
                    jn = sm.get_joint_at(lp, radius=30)
                    if jn:
                        self.active_stickman = sm
                        if self.detach_mode:
                            sm.toggle_detached(jn)
                        else:
                            self.save_undo()
                            sm.selected_joint = jn
                            sm.dragged_joint = jn
                        hit = True
                        self.canvas_dirty = True
                        break
                if not hit and not sms:
                    self.save_undo()
                    self.spawn_stickman()
                elif not hit:
                    self.active_stickman = None
                    self.toolbar_dragging = False
                    self.pan_start_x = pos[0]
                    self.pan_start_y = pos[1]
                    self.pan_start_pan_x = self.pan_x
                    self.pan_start_pan_y = self.pan_y
            elif self.tool == "text":
                self.osk_text_target_pos = lp
                self.osk_buffer = ""
                self.osk_active = True
            elif self.tool == "fill":
                self.save_undo()
                self.bg_color = self.color
                self.canvas_dirty = True
            else:
                self.save_undo()
                self.drawing = True
                self.start_pos = lp
                self.current_points = [lp]

    def _mouse_move(self, event):
        pos = event.pos
        if self.toolbar_dragging:
            dx = pos[0] - self.toolbar_last_mouse_x
            self.toolbar_scroll_x += dx
            max_scroll = -(self.toolbar_total_w - (self.w - (self.side_panel_w if self.side_panel_open else 0)))
            self.toolbar_scroll_x = min(0, max(max_scroll, self.toolbar_scroll_x))
            self.toolbar_last_mouse_x = pos[0]
            return

        if self.tool == "hand" and not self.active_stickman:
            if self.pan_start_x is not None:
                dx = pos[0] - self.pan_start_x
                dy = pos[1] - self.pan_start_y
                self.pan_x = self.pan_start_pan_x + dx
                self.pan_y = self.pan_start_pan_y + dy
                self.clamp_pan()
                self.update_canvas_rect()
            return

        if not self.canvas_rect.collidepoint(pos): return
        lp = self.to_local(pos)
        lp = self.snap_pos(lp)

        if self.tool == "hand" and self.active_stickman:
            sm = self.active_stickman
            if sm.dragged_joint:
                sm.update_joint_pos(sm.dragged_joint, lp, luffy_mode=self.luffy_mode, ragdoll_mode=self.ragdoll_mode)
                self.canvas_dirty = True
        elif self.drawing:
            self.current_points.append(lp)

    def _mouse_up(self, event):
        if event.button != 1: return
        self.toolbar_dragging = False
        self.tap_start_pos = None
        self.touch_down = False

        self.pan_start_x = None
        self.pan_start_y = None
        self.pan_start_pan_x = 0
        self.pan_start_pan_y = 0

        if self.tool == "hand":
            if self.active_stickman:
                self.active_stickman.selected_joint = None
                self.active_stickman.dragged_joint = None
        elif self.drawing:
            self.drawing = False
            if self.tool in ("pen","eraser") and len(self.current_points) > 1:
                pts_copy = [list(p) for p in self.current_points]
                self.frames[self.current_frame].append({
                    "points": pts_copy, "color": self.color,
                    "size": self.brush_size * 3 if self.tool == "eraser" else self.brush_size,
                    "is_eraser": self.tool == "eraser", "tool": self.tool})
                self.canvas_dirty = True
            elif self.tool in ("line","circle","rect","triangle","star"):
                if len(self.current_points) > 0:
                    pts = self.build_shape(self.tool, self.start_pos, self.current_points[-1])
                    if len(pts) > 1:
                        pts_copy = [list(p) for p in pts]
                        self.frames[self.current_frame].append({
                            "points": pts_copy, "color": self.color, "size": self.brush_size,
                            "is_eraser": False, "tool": self.tool})
                        self.canvas_dirty = True
            self.start_pos = None
            self.current_points = []

    def _handle_side_panel_click(self, pos):
        for rect, act in self.side_btn_rects:
            if rect.collidepoint(pos):
                act()
                return

    def _handle_timeline_click(self, pos):
        for rect, act in self.timeline_btns:
            if rect.collidepoint(pos):
                act()
                return
        thumb_w = max(int(75 * self.scale_factor), int(self.w * 0.09))
        thumb_h = max(int(55 * self.scale_factor), int(self.timeline_h * 0.45))
        max_visible = max(1, (self.w - 300) // (thumb_w + 8))
        start_idx = max(0, min(self.current_frame - max_visible//2, len(self.frames) - max_visible))
        end_idx = min(len(self.frames), start_idx + max_visible)
        start_x = self.w - (end_idx - start_idx) * (thumb_w + 8) - 10
        tyy = self.h - thumb_h - 15
        for i in range(start_idx, end_idx):
            rect = pygame.Rect(start_x + (i - start_idx)*(thumb_w+8), tyy, thumb_w, thumb_h)
            if rect.collidepoint(pos):
                self.current_frame = i
                self._update_active()
                return

    def to_local(self, pos):
        z = self.base_zoom * self.zoom
        if z == 0: z = 0.001
        lx = int((pos[0] - self.canvas_rect.x) / z)
        ly = int((pos[1] - self.canvas_rect.y) / z)
        return [lx, ly]

    def snap_pos(self, pos):
        if self.snap_enabled and self.grid_enabled:
            g = 20
            return [round(pos[0]/g)*g, round(pos[1]/g)*g]
        return pos

    def set_tool(self, t):
        if t == "stickman":
            self.side_panel_open = True
            self.build_ui()
        else:
            self.tool = t
            self.text_editing = False
        self.ui_dirty = True

    def zoom_in(self):
        self.zoom = min(3.0, self.zoom + 0.2)
        self.build_ui()
        self.clamp_pan()
        self.update_canvas_rect()

    def zoom_out(self):
        self.zoom = max(0.4, self.zoom - 0.2)
        self.build_ui()
        self.clamp_pan()
        self.update_canvas_rect()

    def inc_brush(self):
        self.brush_size = min(50, self.brush_size + 2)
        self.show_toast(f"Spessore: {self.brush_size}")

    def dec_brush(self):
        self.brush_size = max(1, self.brush_size - 2)
        self.show_toast(f"Spessore: {self.brush_size}")

    def toggle_onion(self):
        self.onion_skin = not self.onion_skin
        self.canvas_dirty = True
        self.show_toast(f"Onion: {'ON' if self.onion_skin else 'OFF'}")

    def toggle_grid(self):
        self.grid_enabled = not self.grid_enabled
        self.canvas_dirty = True
        self.show_toast(f"Griglia: {'ON' if self.grid_enabled else 'OFF'}")

    def toggle_theme(self):
        self.theme_dark = not self.theme_dark
        self.bg_color = C_BLACK if self.theme_dark else C_WHITE
        self.canvas_dirty = True
        self.show_toast(f"Tema: {'Scuro' if self.theme_dark else 'Chiaro'}")

    def toggle_luffy(self):
        self.luffy_mode = not self.luffy_mode
        self.canvas_dirty = True
        self.show_toast(f"Luffy: {'ON' if self.luffy_mode else 'OFF'}")

    def toggle_ragdoll(self):
        self.ragdoll_mode = not self.ragdoll_mode
        sms = self.frame_stickmen.get(self.current_frame, [])
        for sm in sms: sm.set_ragdoll(self.ragdoll_mode)
        self.canvas_dirty = True
        self.show_toast(f"Ragdoll: {'ON' if self.ragdoll_mode else 'OFF'}")

    def toggle_detach(self):
        self.detach_mode = not self.detach_mode
        self.show_toast(f"Stacca: {'ON' if self.detach_mode else 'OFF'}")

    def spawn_stickman(self):
        if self.current_frame not in self.frame_stickmen:
            self.frame_stickmen[self.current_frame] = []
        sm = StickmanDynamic(self.canvas_w//2, self.canvas_h//2)
        sm.ground_y = self.canvas_h
        self.frame_stickmen[self.current_frame].append(sm)
        self.active_stickman = sm
        self.canvas_dirty = True
        self.show_toast("Stickman aggiunto")

    def grow_stickman(self):
        if self.active_stickman:
            self.active_stickman.resize(1.15)
            self.canvas_dirty = True

    def shrink_stickman(self):
        if self.active_stickman:
            self.active_stickman.resize(0.85)
            self.canvas_dirty = True

    def reset_stickman_pose(self):
        if self.active_stickman:
            cx, cy = self.active_stickman.joints["pelvis"].pos.x, self.active_stickman.joints["pelvis"].pos.y
            sc = self.active_stickman.scale
            self.active_stickman.__init__(cx, cy, sc)
            self.active_stickman.ground_y = self.canvas_h
            self.canvas_dirty = True
            self.show_toast("Pose resettata")

    def save_undo(self):
        strokes = [dict(s, points=[list(p) for p in s.get("points",[])]) for s in self.frames[self.current_frame]]
        sms = []
        if self.current_frame in self.frame_stickmen:
            for old in self.frame_stickmen[self.current_frame]:
                sm = StickmanDynamic(0, 0, old.scale)
                for name, j in old.joints.items():
                    sm.joints[name].set_pos(j.pos.x, j.pos.y)
                    sm.joints[name].old_pos = Vec2(j.old_pos.x, j.old_pos.y)
                    sm.joints[name].pinned = j.pinned
                sm.detached = set(old.detached)
                sm.ground_y = old.ground_y
                sms.append(sm)
        self.undo_stack.append({"frame": self.current_frame, "strokes": strokes, "stickmen": sms})
        if len(self.undo_stack) > 20:
            self.undo_stack.pop(0)

    def undo(self):
        if not self.undo_stack:
            self.show_toast("Niente da annullare")
            return
        data = self.undo_stack.pop()
        if data["frame"] == self.current_frame:
            self.frames[self.current_frame] = data["strokes"]
            if data["stickmen"]:
                self.frame_stickmen[self.current_frame] = data["stickmen"]
                self.active_stickman = data["stickmen"][-1]
            else:
                self.frame_stickmen.pop(self.current_frame, None)
                self.active_stickman = None
            self.canvas_dirty = True
            self.show_toast("Annullato")

    def clear_canvas(self):
        self.save_undo()
        self.frames[self.current_frame] = []
        if self.current_frame in self.frame_stickmen:
            self.frame_stickmen[self.current_frame] = []
        self.active_stickman = None
        self.canvas_dirty = True

    def prev_frame(self):
        if self.current_frame > 0:
            self.current_frame -= 1
            self._update_active()

    def next_frame(self):
        if self.current_frame < len(self.frames)-1:
            self.current_frame += 1
            self._update_active()

    def add_frame(self):
        self.frames.append([])
        self.current_frame = len(self.frames)-1
        self._update_active()
        self.build_ui()

    def dup_frame(self):
        dup = [dict(s, points=[list(p) for p in s.get("points",[])]) for s in self.frames[self.current_frame]]
        self.frames.insert(self.current_frame+1, dup)
        new_stickmen = {}
        for k, v in sorted(self.frame_stickmen.items()):
            if k > self.current_frame:
                new_stickmen[k+1] = v
            else:
                new_stickmen[k] = v
        self.frame_stickmen = new_stickmen
        if self.current_frame in self.frame_stickmen:
            new_list = []
            for old in self.frame_stickmen[self.current_frame]:
                sm = StickmanDynamic(0, 0, old.scale)
                for name, j in old.joints.items():
                    sm.joints[name].set_pos(j.pos.x, j.pos.y)
                    sm.joints[name].old_pos = Vec2(j.old_pos.x, j.old_pos.y)
                    sm.joints[name].pinned = j.pinned
                sm.detached = set(old.detached)
                sm.ground_y = old.ground_y
                new_list.append(sm)
            self.frame_stickmen[self.current_frame+1] = new_list
        self.current_frame += 1
        self._update_active()
        self.build_ui()

    def del_frame(self):
        if len(self.frames) <= 1:
            self.show_toast("Non puoi eliminare l'unico frame")
            return
        self.frames.pop(self.current_frame)
        if self.current_frame in self.frame_stickmen:
            del self.frame_stickmen[self.current_frame]
        new_dict = {}
        for k, v in sorted(self.frame_stickmen.items()):
            if k > self.current_frame: new_dict[k-1] = v
            elif k < self.current_frame: new_dict[k] = v
        self.frame_stickmen = new_dict
        if self.current_frame >= len(self.frames):
            self.current_frame = len(self.frames)-1
        self._update_active()
        self.build_ui()

    def _update_active(self):
        sms = self.frame_stickmen.get(self.current_frame, [])
        self.active_stickman = sms[-1] if sms else None
        self.canvas_dirty = True

    def toggle_play(self):
        self.is_playing = not self.is_playing
        self.play_index = 0
        self.play_timer = 0
        self.canvas_dirty = True

    def build_shape(self, tool, start, end):
        cx, cy = start; mx, my = end; dx, dy = mx-cx, my-cy; length = math.hypot(dx, dy); pts = []
        if tool == "line": pts = [[cx,cy],[mx,my]]
        elif tool == "circle":
            r = int(length)
            if r < 1: r = 1
            step = max(15, 360 // (r // 5 + 10))
            for a in range(0, 361, step):
                rad = math.radians(a)
                pts.append([cx+r*math.cos(rad), cy+r*math.sin(rad)])
        elif tool == "rect": pts = [[cx,cy],[mx,cy],[mx,my],[cx,my],[cx,cy]]
        elif tool == "triangle": pts = [[cx,cy],[mx,my],[cx-(mx-cx),my],[cx,cy]]
        elif tool == "star":
            for i in range(10):
                a = math.pi/2 + i*math.pi/5
                rr = length if i%2==0 else length*0.4
                pts.append([cx+rr*math.cos(a), cy-rr*math.sin(a)])
            if pts: pts.append(pts[0])
        return pts

    def save_project(self):
        try:
            data = {"version": VERSION, "frames": [], "stickmen": {}, "settings": {
                "name": self.project_name, "canvas_w": self.canvas_w, "canvas_h": self.canvas_h,
                "fps": self.fps, "bg_color": self.bg_color, "theme_dark": self.theme_dark}}
            for strokes in self.frames:
                fd = []
                for s in strokes:
                    fd.append({"points": s.get("points",[]), "color": s.get("color",C_BLACK),
                        "size": s.get("size",2), "is_eraser": s.get("is_eraser",False),
                        "tool": s.get("tool","pen"), "text": s.get("text","")})
                data["frames"].append(fd)
            for fidx, sms in self.frame_stickmen.items():
                sm_list = []
                for sm in sms:
                    sm_list.append({"scale": sm.scale, "ground_y": sm.ground_y,
                        "joints": {n:{"x":j.pos.x,"y":j.pos.y,"pinned":j.pinned} for n,j in sm.joints.items()},
                        "detached": list(sm.detached)})
                data["stickmen"][str(fidx)] = sm_list
            fname = os.path.join(APP_DIR, f"{self.project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(fname, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            self.show_toast(f"Salvato: {fname}")
        except Exception as e:
            self.show_toast(f"Errore salva: {str(e)}")

    def load_project(self, filename):
        if not os.path.exists(filename):
            self.show_toast("File non trovato")
            return
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.frames = []
            for fd in data.get("frames", []):
                strokes = []
                for s in fd:
                    strokes.append({"points": [list(p) for p in s.get("points",[])],
                        "color": tuple(s.get("color", C_BLACK)), "size": s.get("size",2),
                        "is_eraser": s.get("is_eraser",False), "tool": s.get("tool","pen"), "text": s.get("text","")})
                self.frames.append(strokes)
            self.frame_stickmen = {}
            for fidx_str, sm_list in data.get("stickmen", {}).items():
                fidx = int(fidx_str)
                sms = []
                for sd in sm_list:
                    px = sd["joints"]["pelvis"]["x"]
                    py = sd["joints"]["pelvis"]["y"]
                    sm = StickmanDynamic(px, py, sd.get("scale",1.0))
                    for n, jd in sd["joints"].items():
                        if n in sm.joints:
                            sm.joints[n].set_pos(jd["x"], jd["y"])
                            sm.joints[n].pinned = jd.get("pinned", False)
                    sm.detached = set(sd.get("detached", []))
                    sm.ground_y = sd.get("ground_y", self.canvas_h)
                    sm._build_constraints()
                    for dj in sm.detached:
                        for c in sm.constraints:
                            if c[0]==dj or c[1]==dj: c[3]=False
                    sms.append(sm)
                self.frame_stickmen[fidx] = sms
            st = data.get("settings", {})
            self.project_name = st.get("name", "Progetto")
            self.canvas_w = st.get("canvas_w", 1280)
            self.canvas_h = st.get("canvas_h", 720)
            self.fps = st.get("fps", 12)
            self.theme_dark = st.get("theme_dark", False)
            saved_bg = st.get("bg_color", C_WHITE)
            if isinstance(saved_bg, list) and len(saved_bg) == 3:
                saved_bg = tuple(saved_bg)
            self.bg_color = C_BLACK if self.theme_dark else (saved_bg if isinstance(saved_bg, tuple) else C_WHITE)
            self.current_frame = 0
            self._update_active()
            self.build_ui()
            self.show_toast(f"Caricato: {filename}")
        except Exception as e:
            self.show_toast(f"Errore: {str(e)}")

    def export_png(self):
        try:
            folder = os.path.join(APP_DIR, f"export_{self.project_name}")
            if not os.path.exists(folder): os.makedirs(folder)
            for idx in range(len(self.frames)):
                surf = pygame.Surface((self.canvas_w, self.canvas_h))
                surf.fill(self.bg_color)
                for stroke in self.frames[idx]:
                    pts = stroke.get("points", [])
                    if len(pts) > 1:
                        col = self.bg_color if stroke.get("is_eraser") else stroke.get("color", C_BLACK)
                        pygame.draw.lines(surf, col, False, pts, stroke.get("size", 2))
                    elif stroke.get("tool") == "text" and len(pts) == 1:
                        txt = stroke.get("text", "")
                        if txt:
                            fnt = get_font(max(12, stroke.get("size", 2) * 3))
                            ts = fnt.render(txt, True, stroke.get("color", C_BLACK))
                            surf.blit(ts, (int(pts[0][0]), int(pts[0][1])))
                if idx in self.frame_stickmen:
                    for sm in self.frame_stickmen[idx]:
                        sm.draw(surf, C_BLACK if not self.theme_dark else C_WHITE, False, False, False, self.theme_dark)
                pygame.image.save(surf, os.path.join(folder, f"frame_{idx+1:03d}.png"))
            try:
                from PIL import Image
                imgs = [Image.open(os.path.join(folder, f"frame_{i+1:03d}.png")).convert("RGB") for i in range(len(self.frames))]
                imgs[0].save(os.path.join(folder, "animazione.gif"), save_all=True, append_images=imgs[1:], duration=int(1000/self.fps), loop=0)
                self.show_toast(f"Export OK in {folder}/")
            except ImportError:
                self.show_toast(f"PNG OK (installa Pillow per GIF)")
        except Exception as e:
            self.show_toast(f"Errore export: {str(e)}")

    def update(self, dt):
        if self.current_frame in self.frame_stickmen:
            for sm in self.frame_stickmen[self.current_frame]:
                if self.ragdoll_mode:
                    sm.update_physics(gravity=Vec2(0, 0.6), iterations=3)
                if self.luffy_mode or self.ragdoll_mode:
                    sm.wobble_phase += 0.05
                    self.canvas_dirty = True

        if self.is_playing and len(self.frames) > 0:
            self.play_timer += dt
            fd = 1000.0 / max(1, self.fps)
            if self.play_timer >= fd:
                self.play_timer = 0
                self.play_index += 1
                if self.play_index >= len(self.frames):
                    if self.loop:
                        self.play_index = 0
                    else:
                        self.play_index = len(self.frames)-1
                        self.is_playing = False
                self.canvas_dirty = True

    def run(self):
        while self.running:
            dt = self.clock.tick(30)
            if self.state == "menu":
                self.handle_menu_events()
                self.draw_menu()
            elif self.state == "new_project":
                self.handle_new_project_events()
                self.draw_new_project()
            elif self.state == "settings_menu":
                self.handle_settings_events()
                self.draw_settings_menu()
            elif self.state == "editor":
                self.handle_editor_events()
                self.update(dt)
                self.draw_editor()
        pygame.quit()

if __name__ == "__main__":
    app = App()
    app.run()
