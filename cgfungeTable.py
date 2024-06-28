
TABLE_MAX_HEIGHT = 30
TABLE_MAX_WIDTH = 40
MAX_MOVES_ALLOWED = 3000

class CGFungeTable:
    def __init__(self):

        #Empty table
        self.table = []
        for row in range(TABLE_MAX_HEIGHT):
            self.table.append([" "]*TABLE_MAX_WIDTH)
        
        self.heatmap = []
        self.max_heatmap = 0
        self.annotations = []
        for i in range(TABLE_MAX_HEIGHT):
            self.heatmap.append([0]*TABLE_MAX_WIDTH)
            self.annotations.append([None]*TABLE_MAX_WIDTH)
            for j in range(TABLE_MAX_WIDTH):
                self.annotations[i][j] = dict()
            

    def reset(self):
        for i in range(TABLE_MAX_HEIGHT):
            for j in range(TABLE_MAX_WIDTH):
                self.table[i][j] = " "
        
        self.reset_annotations()
        self.reset_heatmap()

    def reset_annotations(self):
        for i in range(TABLE_MAX_HEIGHT):
            for j in range(TABLE_MAX_WIDTH):
                self.annotations[i][j].clear()
    
    def reset_heatmap(self):
        self.max_heatmap = 0
        for i in range(TABLE_MAX_HEIGHT):
            for j in range(TABLE_MAX_WIDTH):
                self.heatmap[i][j] = 0

    def set_table_from_text(self, raw_table):
        lines = raw_table.replace("\r","").split("\n")

        for i,l in enumerate(lines):
            if i >= TABLE_MAX_HEIGHT: return
            self.table[i] = list(l.ljust(TABLE_MAX_WIDTH)[:TABLE_MAX_WIDTH])
            
        
        for e in range(i+1,TABLE_MAX_HEIGHT):
            self.table[e] = [" "]*TABLE_MAX_WIDTH
        
        self.reset_annotations()
        self.reset_heatmap()

    def to_int32(self,num):
        num = num & 0xffffffff
        if num >= 0x80000000:
            num -= 0x100000000
        return num
    
    def simulate(self, number : int, expected : str) -> int:
        moves=1
        px,py=0,0
        movx,movy=1,0
        ignore_next=False
        str_mode=False
        stack = [number]
        current_action = self.table[py][px]
        if self.heatmap[py][px]>=0:
            self.heatmap[py][px]+=1
            self.max_heatmap = max(self.heatmap[py][px],self.max_heatmap)
        printed_str=""
        while ignore_next or str_mode or current_action!="E":

            if not ignore_next and not str_mode:
                if current_action in "+-*/" and len(stack)<=1:
                    if "error" not in self.annotations[py][px]: self.annotations[py][px]["error"] = []
                    self.annotations[py][px]["error"].append((number, "STACK EMPTY"))
                    self.heatmap[py][px]=-1
                    return -1
                if current_action in "DPX:IC" and len(stack)<=0:
                    if "error" not in self.annotations[py][px]: self.annotations[py][px]["error"] = []
                    self.annotations[py][px]["error"].append((number, "STACK EMPTY"))
                    self.heatmap[py][px]=-1
                    return -1

            if ignore_next:
                ignore_next = False
            elif current_action=="\"":
                str_mode = not str_mode
            elif str_mode:
                stack.append(ord(current_action))
            elif current_action==">":
                movx=1
                movy=0
            elif current_action=="<":
                movx=-1
                movy=0
            elif current_action=="^":
                movx=0
                movy=-1
            elif current_action=="v":
                movx=0
                movy=1
            elif current_action=="S":
                ignore_next = True
            elif current_action in "0123456789":
                stack.append(int(current_action))
            elif current_action=="+":
                second = stack[-1]
                stack = stack[:-1]
                stack[-1]+=second
                stack[-1]=self.to_int32(stack[-1])
            elif current_action=="-":
                second = stack[-1]
                stack = stack[:-1]
                stack[-1]-=second
                stack[-1]=self.to_int32(stack[-1])
            elif current_action=="*":
                second = stack[-1]
                stack = stack[:-1]
                stack[-1]*=second
                stack[-1]=self.to_int32(stack[-1])
            elif current_action=="/":
                second = stack[-1]
                stack = stack[:-1]
                if second == 0:
                    if "error" not in self.annotations[py][px]: self.annotations[py][px]["error"] = []
                    self.annotations[py][px]["error"].append((number, "DIVISION BY 0"))
                    self.heatmap[py][px]=-1
                    return -1
                stack[-1]= stack[-1]//second
                stack[-1]=self.to_int32(stack[-1])
            elif current_action=="P":
                stack = stack[:-1]
            elif current_action=="X":
                index=stack[-1]
                stack = stack[:-1]
                if index>=len(stack):
                    if "error" not in self.annotations[py][px]: self.annotations[py][px]["error"] = []
                    self.annotations[py][px]["error"].append((number, "STACK UNDERFLOW"))
                    self.heatmap[py][px]=-1
                    return -1
                stack = stack[:-index-1]+stack[-index:]+[stack[-index-1]]
            elif current_action=="D":
                stack.append(stack[-1])
            elif current_action==":":
                sign= max(min(stack[-1],1),-1)
                stack = stack[:-1]
                if sign!=0:
                    movx,movy = -movy * sign, movx * sign
            elif current_action=="I":
                printed_str+=str(stack[-1])
                stack = stack[:-1]
            elif current_action=="C":
                printed_str+=chr(stack[-1])
                stack = stack[:-1]
            
            px+=movx
            py+=movy
            moves+=1

            if px>=TABLE_MAX_WIDTH or py>=TABLE_MAX_HEIGHT or px<0 or py<0:
                self.heatmap[py-movy][px-movx]=-1
                if "error" not in self.annotations[py-movy][px-movx]: self.annotations[py-movy][px-movx]["error"] = []
                self.annotations[py-movy][px-movx]["error"].append((number, "OUT OF BOUNDS"))
                return -1
        
            if moves>MAX_MOVES_ALLOWED:
                self.heatmap[py-movy][px-movx]=-1
                if "error" not in self.annotations[py-movy][px-movx]: self.annotations[py-movy][px-movx]["error"] = []
                self.annotations[py-movy][px-movx]["error"].append((number, "MAX TURNS"))
                return -1

            current_action = self.table[py][px]
            if self.heatmap[py][px]>=0:
                self.heatmap[py][px]+=1
                self.max_heatmap = max(self.heatmap[py][px],self.max_heatmap)

        #check print string (set -1)
        if printed_str!=expected:
            moves=-1
            if "fails" not in self.annotations[py][px]: self.annotations[py][px]["fails"] = []
            self.annotations[py][px]["fails"].append((number, printed_str, expected))
            self.heatmap[py][px]=-1

        return moves

if __name__=="__main__":
    input("You need to execute 'visual_table.py' (this program is a dependency). Press enter to finish the program.")