#coding:utf-8

import struct
from collections import namedtuple

class VOX(object):
    
    # 初始化 - 读取数据到内存
    def __init__(self,path):
        self.__path = path
        with open(self.__path, 'rb') as f:
            self.__DATA = f.read()
        self.__SIZE_chunk = []
        self.__SIZE_content = []
        self.__XYZI_chunk = []
        self.__XYZI_content = []
        self.__MATT_chunk = []
        self.__MATT_content = []

            
    # 构造元组 - 自定义结构
    def StructureTuple(self, typename, field_name, format, data):
        structureTuple = namedtuple(typename, field_name)
        Instance = (structureTuple._make(struct.unpack(format, data)))
        return Instance

    # 构造元组 - 标准Chunk基础结构
    def ChunkStruct(self, typename, cursor):
        structureTuple = namedtuple(typename, 'chunk_id contentSize childrenSize')
        Instance = (structureTuple._make(struct.unpack('4sii', self.__DATA[cursor:cursor + 12])))
        return Instance

    # 返回FLAG
    def Get_FLAG(self, Setdata = ''):
        if Setdata == '' :
            return self.__FLAG

    # 返回XYZI块的颜色映射
    def Get_XYZI_ColorMapping(self, numModule = 0,Setdata = ''):
        if Setdata == '' :
            ColorMapping = []
            # 循环读出像素格颜色信息
            for i in range(self.__XYZI_content[numModule].numVoxels):
                ColorMapping.append(struct.unpack('4B', self.__XYZI_content[numModule].colorMapping[i * 4 : i * 4 + 4]))
            return ColorMapping

    # 返回RGBA块的调色盘
    def Get_RGBA_Palette(self, Setdata = ''):
        if Setdata == '' :
            Palette = []
            # 循环读出调色盘颜色信息
            for i in range(256):
                Palette.append(struct.unpack('4B', self.__RGBA_content.Palette[i * 4 : i * 4 + 4]))
            return Palette

    # 返回MATT块的单位化特征值
    def Get_MATT_NormalizedPropertyValue(self, numMATT = 0,Setdata = ''):
        if Setdata == '' :
            NormalizedPropertyValue = []
            # 循环读出单位化特征值
            for i in range((self.__MATT_chunk[numMATT].contentSize - 16) / 4):
                NormalizedPropertyValue.append(struct.unpack('f', self.__MATT_content[numMATT].normalizedPropertyValue[i * 4 : i * 4 + 4])[0])
            return NormalizedPropertyValue

    # 解析VOX文件
    def Parser(self):
        # 初始化游标
        cursor = 0
        
        # 判断文件格式 RIFF style
        self.__FLAG = self.StructureTuple('__FLAG', 'Id Version', '4si', self.__DATA[cursor : cursor + 8])
        cursor += 8
        if(self.__FLAG.Id != 'VOX '):
            pass
            # 抛出异常 - 文件格式错误

        # 读取MAIN块 the root chunk and parent chunk of all the other chunks
        self.__MAIN_chunk = self.ChunkStruct('__MAIN_chunk', cursor)
        cursor += 12

        # 读取PACK块(optional) if it is absent, only one model in the file
        self.__PACK_chunk = self.ChunkStruct('__PACK_chunk', cursor)
        if(self.__PACK_chunk.chunk_id == 'PACK'):
            self.__PACK_content = self.StructureTuple('__PACK_content', 'numModels', 'i', self.__DATA[cursor + 12 : cursor + self.__PACK_chunk.contentSize + 12])
            cursor += self.__PACK_chunk.contentSize + 12

        if(self.__PACK_chunk.chunk_id == 'PACK'):
            modelCount = self.__PACK_content.numModels
        else:
            modelCount = 1

        # 循环读取SIZE块和XYZI块
        for numModel in range(0, modelCount):
            
            # 读取SIZE块 model size
            SIZE_chunk = self.ChunkStruct('__SIZE_chunk', cursor)
            SIZE_content = self.StructureTuple('__SIZE_content', 'size_x size_y size_z', 'iii', self.__DATA[cursor + 12 : cursor  + SIZE_chunk.contentSize + 12])
            cursor += SIZE_chunk.contentSize + 12
            self.__SIZE_chunk.append(SIZE_chunk)
            self.__SIZE_content.append(SIZE_content)

            # 读取XYZI块 model voxels
            __XYZI_chunk = self.ChunkStruct('__XYZI_chunk', cursor)
            __XYZI_content = self.StructureTuple('__XYZI_content', 'numVoxels colorMapping', 'i' + str(__XYZI_chunk.contentSize - 4) + 's', self.__DATA[cursor + 12 : cursor + __XYZI_chunk.contentSize + 12])
            cursor += __XYZI_chunk.contentSize + 12
            self.__XYZI_chunk.append(__XYZI_chunk)
            self.__XYZI_content.append(__XYZI_content)

        if(cursor - 20 >= self.__MAIN_chunk.childrenSize): return # __FLAG 8字节 + __MAIN 12字节

        # 读取RGBA块(optional) palette
        self.__RGBA_chunk = self.ChunkStruct('__RGBA_chunk', cursor)
        if(self.__RGBA_chunk.chunk_id == 'RGBA'):
            self.__RGBA_content = self.StructureTuple('__RGBA_content', 'Palette', '1024s', self.__DATA[cursor + 12 : cursor + self.__RGBA_chunk.contentSize + 12])
            cursor += self.__RGBA_chunk.contentSize + 12

        # 读取MATT块(optional) material, if it is absent, it is diffuse material
        while(cursor - 20 < self.__MAIN_chunk.childrenSize):
            MATT_chunk = self.ChunkStruct('__MATT_chunk', cursor)
            if(MATT_chunk.chunk_id == 'MATT'):
                MATT_content = self.StructureTuple('__MATT_content', 'Id materialType materialWeight propertyBits normalizedPropertyValue', \
                                                   'iifi' + str(MATT_chunk.contentSize - 16) + 's', self.__DATA[cursor + 12 : cursor + MATT_chunk.contentSize + 12])
                cursor += MATT_chunk.contentSize + 12
                self.__MATT_chunk.append(MATT_chunk)
                self.__MATT_content.append(MATT_content)



        print '->',self.__DATA[cursor:],'<--'

    def __str__(self):
        Information = ''
        
        Information += '---+[Id] ' + str(self.__FLAG.Id)
        Information += '\n' + '   |----[Version] ' + str(self.__FLAG.Version)

        Information += '\n' + '---+[chunk_id] ' + str(self.__MAIN_chunk.chunk_id)
        Information += '\n' + '   |----[contentSize] ' + str(self.__MAIN_chunk.contentSize)
        Information += '\n' + '   |----[childrenSize]' + str(self.__MAIN_chunk.childrenSize)

        Information += '\n' + '---+[chunk_id] ' + str(self.__PACK_chunk.chunk_id)
        Information += '\n' + '   |----[contentSize]  ' + str(self.__PACK_chunk.contentSize)
        Information += '\n' + '   |----[childrenSize] ' + str(self.__PACK_chunk.childrenSize)
        Information += '\n' + '   |----[numModels]    ' + str(self.__PACK_content.numModels)

        for i in range(len(self.__SIZE_chunk)):
            Information += '\n' + '---+[chunk_id]' + str(self.__SIZE_chunk[i].chunk_id)
            Information += '\n' + '   |----[contentSize]  ' + str(self.__SIZE_chunk[i].contentSize)
            Information += '\n' + '   |----[childrenSize] ' + str(self.__SIZE_chunk[i].childrenSize)
            Information += '\n' + '   |----[size_x] ' + str(self.__SIZE_content[i].size_x)
            Information += '\n' + '   |----[size_y] ' + str(self.__SIZE_content[i].size_y)
            Information += '\n' + '   |----[size_z] ' + str(self.__SIZE_content[i].size_z)

            Information += '\n' + '---+[chunk_id]' + str(self.__XYZI_chunk[i].chunk_id)
            Information += '\n' + '   |----[contentSize]  ' + str(self.__XYZI_chunk[i].contentSize)
            Information += '\n' + '   |----[childrenSize] ' + str(self.__XYZI_chunk[i].childrenSize)
            Information += '\n' + '   |----[numVoxels]    ' + str(self.__XYZI_content[i].numVoxels)
            Information += '\n' + '   |----[colorMapping]' + ' '.join(map(str,self.Get_XYZI_ColorMapping()))


        Information += '\n' + '---+[chunk_id]' + str(self.__RGBA_chunk.chunk_id)
        Information += '\n' + '   |----[contentSize]  ' + str(self.__RGBA_chunk.contentSize)
        Information += '\n' + '   |----[childrenSize] ' + str(self.__RGBA_chunk.childrenSize)
        Information += '\n' + '   |----[Palette] ' + ''.join(map(str,self.Get_RGBA_Palette()))

        for i in range(len(self.__MATT_chunk)):
            Information += '\n' + '---+[chunk_id]' + str(self.__MATT_chunk[i].chunk_id)
            Information += '\n' + '   |----[contentSize]  ' + str(self.__MATT_chunk[i].contentSize)
            Information += '\n' + '   |----[childrenSize] ' + str(self.__MATT_chunk[i].childrenSize)
            Information += '\n' + '   |----[Id]           ' + str(self.__MATT_content[i].Id)
            Information += '\n' + '   |----[materialType] ' + str(self.__MATT_content[i].materialType)
            Information += '\n' + '   |----[materialWeight] ' + str(self.__MATT_content[i].materialWeight)
            Information += '\n' + '   |----[propertyBits]   ' + str(self.__MATT_content[i].propertyBits)
            Information += '\n' + '   |----[normalizedPropertyValue] ' + ' '.join(map(str, self.Get_MATT_NormalizedPropertyValue(i)))

        return Information

    __repr__ = __str__
