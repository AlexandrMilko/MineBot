import time
import json
import threading
import math

from minecraft.networking.connection import Connection, PlayingReactor
from minecraft.networking.packets.serverbound.play import ChatPacket, ClientStatusPacket,  PositionAndLookPacket, UseItemPacket, PlayerBlockPlacementPacket
from minecraft.networking.packets.clientbound.play import ChatMessagePacket, PlayerPositionAndLookPacket, BlockChangePacket
from minecraft.networking.packets.clientbound.status import ResponsePacket, PingResponsePacket
from minecraft.networking.packets import Packet, PositionAndLookPacket, PlayerPositionAndLookPacket
from minecraft.networking.types import Position, VarInt, Boolean, Byte, BlockFace, Long, Float, RelativeHand


        
# CHUNK DATA PACKET START

from collections import defaultdict, namedtuple
from minecraft.networking.packets import Packet
from minecraft.networking.types import (
    Integer, Boolean, VarInt, VarIntPrefixedByteArray, TrailingByteArray,
    UnsignedShort
)


class ChunkDataPacket(Packet):
    @staticmethod
    def get_id(context):
        return 0x22 if context.protocol_version >= 389 else \
               0x21 if context.protocol_version >= 345 else \
               0x20 if context.protocol_version >= 332 else \
               0x21 if context.protocol_version >= 318 else \
               0x20 if context.protocol_version >= 70 else \
               0x21

    packet_name = 'chunk data'

    def read(self, file_object):
        '''
            A chunk is 16x256x16 (x y z) blocks.
            Each chunk has 16 chunk sections where each section represents 16x16x16 blocks.
            The number of chunk sections is equal to the number of bits set in Primary Bit Mask.

            Chunk: 
               Section:
                  Block Data:    2 bytes per block. Total 8192 bytes. format: blockId << 4 | meta
                  Emitted Light: 4 bits per block (1/2 byte). Total 2048 bytes
                  Skylight:      4 bits per block (1/2 byte). Total 2048 bytes (only included in overworld)
               Biome: 1 byte per block column. 256 bytes. (only included if all sections are in chunk)
        '''
        self.chunk_x = Integer.read(file_object)
        self.chunk_z = Integer.read(file_object)
        self.full = Boolean.read(file_object)

        if self.context.protocol_version >= 107:
            self.mask = VarInt.read(file_object)
        else:
            self.mask = UnsignedShort.read(file_object)

        # size of data in bytes 
        self.data_size = VarInt.read(file_object)
        self.read_chunk_column(file_object)
        # TODO
        # self.num_block_entities = VarInt.read(file_object)
        # self.block_entities = TrailingByteArray.read(file_object)

    def read_chunk_column(self, file_object):
        chunk_height = 256
        section_height, section_width = (16, 16)
        Block = namedtuple('Block', 'x y z')

        # section_count = bin(self.mask & 0xFFFF).count('1')
        for section_y in range(chunk_height // section_height):			# MY CHANGE / >> //
            if self.mask & (1 << section_y):

                # read block data - 2 bytes per block
                for y in range(section_height):
                    for z in range(section_width):
                        for x in range(section_width):
                            block = Block(x, y, z)
                            print(dir(file_object.bytes))
                            print(file_object.bytes.get_value)
                            block_data = UnsignedShort.read(file_object)
                            # TODO store


                # read emitted light - 4 bits per block (1/2 byte)
                for y in range(section_height):
                    for z in range(section_width):
                        for x in range(0, section_width, 2):
                             emitted_light = UnsignedByte.read(file_object)
                             # TODO store
                             Block(x, y, z).setBlockLight(emitted_light & 0xF)
                             Block(x + 1, y, z).setBlockLight((emitted_light >> 4) & 0xF)

                # calculate what is left in the packet
                # self.data_size = size of data in bytes 
                # Block Data:    2 bytes per block. Total 8192 bytes.
                # Emitted Light: 4 bits per block (1/2 byte).
                # Skylight:      4 bits per block (1/2 byte).
                block_data_size = section_height * section_width * section_width * 2
                emitted_light_size = section_height * section_width * section_width / 2
                skylight_size = section_height * section_width * section_width / 2

                expected_size = block_data_size + emitted_light_size
                expected_size = expected_size + skylight_size if self.full else 0

                has_skylight = self.data_size > expected_size

                if has_skylight:
                    # read skylight - 4 bits per block (1/2 byte)
                    for y in range(section_height):
                        for z in range(section_width):
                            for x in range(0, section_width, 2):
                                 emitted_light = UnsignedByte.read(file_object)
                                 # TODO store
                                 Block(x, y, z).setSkyLight(emitted_light & 0xF)
                                 Block(x + 1, y, z).setSkyLight((emitted_light >> 4) & 0xF)

        if self.full:
            for z in range(section_width):
                for x in range(section_width):
                    biome = UnsignedByte.read(file_object)

class MapChunkBulkPacket(Packet):
    # Note: removed with protocol versions 69
    id = 0x21

    packet_name = 'map chunk bulk'

    def read(self, file_object):
        self.skylight = Boolean.read(file_object)
        columns = VarInt.read(file_object)
        self.chunk_columns = []
        for i in range(columns):
            record = ChunkDataPacket.read(file_object)
            self.chunk_columns.append(record)

    def write_fields(self, packet_buffer):
        Boolean.send(self.skylight, packet_buffer)
        Integer.send(len(self.chunk_columns), packet_buffer)
        for chunk_column in self.chunk_columns:
            chunk_column.write_fields(packet_buffer)


def add_play_packets(func):
	def wrap(func,context):
		packets=func(context)
		packets.add(ChunkDataPacket)
		return packets
	return staticmethod(lambda x:wrap(func,x))
PlayingReactor.get_clientbound_packets=add_play_packets(PlayingReactor.get_clientbound_packets)



#CHUNK DATA END

class KeepAliveClientboundPacket(Packet):                              #Probably not needed
    id = 0x1F
    packet_name = "Keep Alive Clientbound"
    definition = staticmethod(lambda context: [
        {'keep_alive_id': Long} if context.protocol_later_eq(339)
        else {'keep_alive_id': VarInt}
    ])

class KeepAliveServerboundPacket(Packet):                              #Probably not needed
    id = 0x10
    packet_name = "Keep Alive Serverbound"
    definition = staticmethod(lambda context: [
        {'keep_alive_id': Long} if context.protocol_later_eq(339)
        else {'keep_alive_id': VarInt}
    ])

class DigPacket(Packet):
    # INFO!     IF WE DONT USE get_id - bot gets kicked
    @staticmethod
    def get_id(context):
        return 0x1A if context.protocol_later_eq(464) else \
                    0x18 if context.protocol_later_eq(389) else \
                        0x16 if context.protocol_later_eq(386) else \
                            0x13 if context.protocol_later_eq(343) else \
                                0x14 if context.protocol_later_eq(332) else \
                                    0x14 if context.protocol_later_eq(318) else \
                                        0x13 if context.protocol_later_eq(80) else \
                                            0x11 if context.protocol_later_eq(77) else \
                                                0x10 if context.protocol_later_eq(67) else \
                                                    0x1A

    packet_name = 'Player Digging'
    definition = [{'status': VarInt}, 
                {'location': Position}, 
                {'face': Byte}]

# class PlayerBlockPlacementPacket(Packet):
#     id = 0x2E
#     packet_name = 'Player Block Placement'
#     definition = [
#         {"hand": VarInt},
#         {"location": Position},
#         {'face': VarInt},
#         {'cursor_position_x': Float},
#         {'cursor_position_y': Float},
#         {'cursor_position_z': Float},
#         {'inside_block': Boolean}
#     ]
#
#     Hand = RelativeHand
#     Face = BlockFace

class Bot:
    RESPAWN_PERIOD = 5
    MOVE_DELAY = 0.1
    ONLINE_MODE = True
    def __init__(self, command_object):
        self.USERNAME = command_object.username # Nickname string
        self.ip = command_object.ip # Server's ip
        self.port = command_object.port # Server's port

        # Optional properties
        # self.RESPAWN_PERIOD = command_object.respawn_period
        # self.MOVE_DELAY = command_object.move_delay      # !!!!! ADD THEIR CUSTOMIZATION THROUGH APP !!!!
        # self.ONLINE_MODE = command_object.online_mode
        
        # Bot stats
        self.bot_pos = {
            'x': None,
            'feet_y': None,
            'z': None,
            'yaw': None,
            'pitch': None,
            }
        
        # Connecting bot to the server
        self.connection = Connection(self.ip, self.port, username=self.USERNAME)
        self.connection.connect()
            
        # For respawning
        threading.Timer(self.RESPAWN_PERIOD, self.respawn).start()

        @self.connection.listener(ChunkDataPacket)
        def read_chunk(packet):
            print(packet, "YAY!!!!!!!!!!!!!!!!")

        # Listenting for messages in chat
        @self.connection.listener(ChatMessagePacket)
        def get_msg(chat_packet):
            try:
                print(json.loads(chat_packet.json_data))
            except KeyError:
                print('WARNING: KeyError OCCURED!')
                
        # Getting the position of the client
        @self.connection.listener(PlayerPositionAndLookPacket)
        def get_pos(pos_look_packet):
            self.bot_pos['x'] = pos_look_packet.x
            self.bot_pos['feet_y'] = pos_look_packet.y
            self.bot_pos['z'] = pos_look_packet.z
            self.bot_pos['yaw'] = pos_look_packet.yaw
            self.bot_pos['pitch'] = pos_look_packet.pitch
            print('changed')

        @self.connection.listener(KeepAliveClientboundPacket)                                   #Probably not needed
        def respond_to_keep_alive_packet(keep_alive_clientbound_packet):
            print('client responding to a keep_alive_packet has began')
            self.respond_packet = KeepAliveServerboundPacket()
            self.respond_packet.keep_alive_id = keep_alive_clientbound_packet.keep_alive_id
            self.connection.write_packet(self.respond_packet)

    # Movement of the client
    def move(self, command_object):
        axis = command_object.axis
        steps = command_object.steps
        try:
            if all(self.bot_pos.values()) and (axis=='x' or axis=='feet_y' or axis=='z'):
                self.bot_pos[axis] += steps
                pos_look_packet = PositionAndLookPacket(x=self.bot_pos['x'],
                                                            feet_y=self.bot_pos['feet_y'],
                                                            z=self.bot_pos['z'],
                                                            yaw=self.bot_pos['yaw'],
                                                            pitch=self.bot_pos['pitch'],
                                                            on_ground=True)
                self.connection.write_packet(pos_look_packet)
                time.sleep(self.MOVE_DELAY)
        except KeyError as e:
            print('WARNING: ', e)

    def write_message(self, command_object):
        message = command_object.message
        msg_packet = ChatPacket()
        msg_packet.message = str(message)
        self.connection.write_packet(msg_packet)
        
    # Respawning method
    def respawn(self):
        self.respawn_packet = ClientStatusPacket()
        self.respawn_packet.action_id = ClientStatusPacket().RESPAWN
        self.connection.write_packet(self.respawn_packet)
        threading.Timer(self.RESPAWN_PERIOD, self.respawn).start()

    # Block placing method
    def place_block(self, command_object):
        offset_x = int(command_object.offset_x)
        offset_y = int(command_object.offset_y)
        offset_z = int(command_object.offset_z)
        blockface_str = command_object.blockface_str
        inside_block = command_object.inside_block
        hand = command_object.hand
        try:
            self.place_block_packet = PlayerBlockPlacementPacket()

            self.place_block_packet.location = Position(
                x=int(self.bot_pos['x'])+offset_x,
                y=int(self.bot_pos['feet_y'])+offset_y,
                z=int(self.bot_pos['z'])+offset_z
                )
            if blockface_str.lower() == 'bottom': self.place_block_packet.face = self.place_block_packet.Face.BOTTOM
            elif blockface_str.lower() == 'top': self.place_block_packet.face = self.place_block_packet.Face.TOP
            elif blockface_str.lower() == 'north': self.place_block_packet.face = self.place_block_packet.Face.NORTH
            elif blockface_str.lower() == 'south': self.place_block_packet.face = self.place_block_packet.Face.SOUTH
            elif blockface_str.lower() == 'west': self.place_block_packet.face = self.place_block_packet.Face.WEST
            elif blockface_str.lower() == 'east': self.place_block_packet.face = self.place_block_packet.Face.EAST
            else: return False
            self.place_block_packet.inside_block = inside_block
            self.place_block_packet.hand = hand
            # block data # WAIT does it matter at all??
            self.place_block_packet.x = 0.75
            self.place_block_packet.y = 0.75
            self.place_block_packet.z = 1.0
            print(self.place_block_packet.location, "LOCATION")
            print(self.place_block_packet.face, "FACE")
            print(self.place_block_packet.inside_block, "inside_block")
            print(self.place_block_packet.hand, "hand")
            print(self.place_block_packet.x, "cursor_x")
            print(self.place_block_packet.y, "cursor_y")
            print(self.place_block_packet.z, "cursor_z")
            self.connection.write_packet(self.place_block_packet)
            print("Place_block command has been executed, line 151, bot.py")

            return True

        except TypeError:
            print('PLAYER_BLOCKPLACE METHOD type error, line 165, bot.py')

    def dig_block(self, command_object):
        offset_x = int(command_object.offset_x)
        offset_y = int(command_object.offset_y)
        offset_z = int(command_object.offset_z)
        digging_time = float(command_object.dig_time)

        self.packet = DigPacket()

        self.packet.status = 0
        self.packet.location = Position(
                                        x=int(self.bot_pos['x'])+offset_x,
                                        y=int(self.bot_pos['feet_y'])+offset_y,
                                        z=int(self.bot_pos['z'])+offset_z
                                        )
        self.packet.face = 1

        self.connection.write_packet(self.packet)

        time.sleep(digging_time)

        self.packet.status = 2

        self.connection.write_packet(self.packet)

    def use_current_item(self, command_object): # hand - "MAIN" or "OFF"
        hand = command_object.hand
        self.packet = UseItemPacket()

        if hand == "MAIN":
            self.packet.hand = self.packet.Hand.MAIN
        elif hand == "OFF":
            self.packet.hand = self.packet.Hand.OFF

        self.connection.write_packet(self.packet)

    def sleep(self, command_object):
        time.sleep(command_object.delay)
