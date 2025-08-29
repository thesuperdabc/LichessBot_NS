import os
import platform
import time
import asyncio
from collections import defaultdict

import chess

import psutil

from api import API
from botli_dataclasses import Chat_Message, Game_Information
from config import Config
from lichess_game import Lichess_Game
from openings_db import get_opening_info
from enums import Variant


class Chatter:
    def __init__(self,
                 api: API,
                 config: Config,
                 username: str,
                 game_information: Game_Information,
                 lichess_game: Lichess_Game
                 ) -> None:
        self.api = api
        self.username = username
        self.game_info = game_information
        self.lichess_game = lichess_game
        self.cpu_message = self._get_cpu()
        self.draw_message = self._get_draw_message(config)
        self.name_message = self._get_name_message(config.version)
        self.ram_message = self._get_ram()
        self.player_greeting = self._format_message(config.messages.greeting)
        self.player_goodbye = self._format_message(config.messages.goodbye)
        self.spectator_greeting = self._format_message(config.messages.greeting_spectators)
        self.spectator_goodbye = self._format_message(config.messages.goodbye_spectators)
        self.print_eval_rooms: set[str] = set()
        self.hint_counter: int = 0

    async def handle_chat_message(self, chatLine_Event: dict) -> None:
        chat_message = Chat_Message.from_chatLine_event(chatLine_Event)

        if chat_message.username == 'lichess':
            if chat_message.room == 'player':
                print(chat_message.text)
            return

        if chat_message.username != self.username:
            prefix = f'{chat_message.username} ({chat_message.room}): '
            output = prefix + chat_message.text
            if len(output) > 128:
                output = f'{output[:128]}\n{len(prefix) * " "}{output[128:]}'

            print(output)

        if chat_message.text.startswith('!'):
            await self._handle_command(chat_message)
        elif chat_message.text.lower() in ['firsthint', 'secondhint', 'thirdhint', 'fourthhint', 'fifthhint', 'sixthhint', 'seventhhint']:
            await self._handle_hint_variation(chat_message)

    async def print_eval(self) -> None:
        if not self.game_info.increment_ms and self.lichess_game.own_time < 30.0:
            return

        for room in self.print_eval_rooms:
            await self._send_last_message(room)

    async def send_greetings(self) -> None:
        if self.player_greeting:
            await self.api.send_chat_message(self.game_info.id_, 'player', self.player_greeting)

        if self.spectator_greeting:
            await self.api.send_chat_message(self.game_info.id_, 'spectator', self.spectator_greeting)

    async def send_goodbyes(self) -> None:
        if self.lichess_game.is_abortable:
            return

        if self.player_goodbye:
            await self.api.send_chat_message(self.game_info.id_, 'player', self.player_goodbye)

        if self.spectator_goodbye:
            await self.api.send_chat_message(self.game_info.id_, 'spectator', self.spectator_goodbye)

    async def send_abortion_message(self) -> None:
        await self.api.send_chat_message(self.game_info.id_, 'player', ('Too bad you weren\'t there. '
                                                                        'Feel free to challenge me again, '
                                                                        'I will accept the challenge if possible.'))

    async def _handle_command(self, chat_message: Chat_Message) -> None:
        command = chat_message.text[1:].lower()
        
        match command:
            case 'cpu':
                await self.api.send_chat_message(self.game_info.id_, chat_message.room, self.cpu_message)
            case 'draw':
                await self.api.send_chat_message(self.game_info.id_, chat_message.room, self.draw_message)
            case 'eval':
                await self._send_last_message(chat_message.room)
            case 'motor':
                await self.api.send_chat_message(self.game_info.id_, chat_message.room, self.lichess_game.engine.name)
            case 'name':
                await self.api.send_chat_message(self.game_info.id_, chat_message.room, self.name_message)
            case 'opening':
                if self.game_info.variant != Variant.STANDARD:
                    await self.api.send_chat_message(self.game_info.id_, chat_message.room,
                                                     "Opening names are only available for standard chess.")
                else:
                    move_stack = []
                    if self.lichess_game.board.move_stack:
                        temp_board = chess.Board()
                        for move in self.lichess_game.board.move_stack:
                            move_stack.append(temp_board.san(move))
                            temp_board.push(move)
                    opening_name, move_line = get_opening_info(move_stack)
                    await self.api.send_chat_message(self.game_info.id_, chat_message.room,
                                                     f"Current opening: {opening_name} ({move_line})")
            case 'printeval':
                if not self.game_info.increment_ms and self.game_info.initial_time_ms < 180_000:
                    await self._send_last_message(chat_message.room)
                    return

                if chat_message.room in self.print_eval_rooms:
                    return

                self.print_eval_rooms.add(chat_message.room)
                await self.api.send_chat_message(self.game_info.id_,
                                                 chat_message.room,
                                                 'Type !quiet to stop eval printing.')
                await self._send_last_message(chat_message.room)
            case 'quiet':
                self.print_eval_rooms.discard(chat_message.room)
            case 'pv':
                if chat_message.room == 'player':
                    return

                if not (message := self._append_pv()):
                    message = 'No PV available.'

                await self.api.send_chat_message(self.game_info.id_, chat_message.room, message)
            case 'ram':
                await self.api.send_chat_message(self.game_info.id_, chat_message.room, self.ram_message)


            case 'book':
                if self.lichess_game.book_settings.readers:
                    book_names = ", ".join(self.lichess_game.book_settings.readers.keys())
                    await self.api.send_chat_message(self.game_info.id_, chat_message.room,
                                                     f"Using opening books: {book_names}")
                else:
                    await self.api.send_chat_message(self.game_info.id_, chat_message.room,
                                                     "Not using any opening books.")
            case 'egtb':
                egtb_info = []
                if self.lichess_game.syzygy_tablebase:
                    egtb_info.append(f"Syzygy (up to {self.lichess_game.syzygy_config.max_pieces} pieces)")
                if self.lichess_game.gaviota_tablebase:
                    egtb_info.append(f"Gaviota (up to {self.lichess_game.config.gaviota.max_pieces} pieces)")
                if egtb_info:
                    await self.api.send_chat_message(self.game_info.id_, chat_message.room,
                                                     f"Using endgame tablebases: {', '.join(egtb_info)}")
                else:
                    await self.api.send_chat_message(self.game_info.id_, chat_message.room,
                                                     "Not using any endgame tablebases.")
            case 'stats':
                material = {
                    chess.PAWN: len(self.lichess_game.board.pieces(chess.PAWN, chess.WHITE)) - len(self.lichess_game.board.pieces(chess.PAWN, chess.BLACK)),
                    chess.KNIGHT: len(self.lichess_game.board.pieces(chess.KNIGHT, chess.WHITE)) - len(self.lichess_game.board.pieces(chess.KNIGHT, chess.BLACK)),
                    chess.BISHOP: len(self.lichess_game.board.pieces(chess.BISHOP, chess.WHITE)) - len(self.lichess_game.board.pieces(chess.BISHOP, chess.BLACK)),
                    chess.ROOK: len(self.lichess_game.board.pieces(chess.ROOK, chess.WHITE)) - len(self.lichess_game.board.pieces(chess.ROOK, chess.BLACK)),
                    chess.QUEEN: len(self.lichess_game.board.pieces(chess.QUEEN, chess.WHITE)) - len(self.lichess_game.board.pieces(chess.QUEEN, chess.BLACK))
                }
                
                material_score = (material[chess.PAWN] * 1 +
                                 material[chess.KNIGHT] * 3 +
                                 material[chess.BISHOP] * 3 +
                                 material[chess.ROOK] * 5 +
                                 material[chess.QUEEN] * 9)
                
                total_pieces = len(self.lichess_game.board.piece_map())
                if total_pieces > 20:
                    phase = "Opening"
                elif total_pieces > 10:
                    phase = "Middlegame"
                else:
                    phase = "Endgame"
                
                turn = "White" if self.lichess_game.board.turn else "Black"
                move_number = self.lichess_game.board.fullmove_number
                
                message = (f"Position stats: Material advantage: {material_score} "
                          f"(P:{material[chess.PAWN]} N:{material[chess.KNIGHT]} B:{material[chess.BISHOP]} "
                          f"R:{material[chess.ROOK]} Q:{material[chess.QUEEN]}), "
                          f"Phase: {phase}, Turn: {turn} (move {move_number})")
                
                await self.api.send_chat_message(self.game_info.id_, chat_message.room, message)
            case 'help' | 'commands':
                try:
                    if chat_message.room == 'player':
                        message = 'Supported commands: !cpu, !draw, !eval, !game, !motor, !name, !opening, !ping, !printeval, !hint, !ram, !book, !egtb, !stats. For hints in casual games: firsthint, secondhint, etc.'
                    else:
                        message = 'Supported commands: !cpu, !draw, !eval, !game, !motor, !name, !opening, !ping, !printeval, !pv, !hint, !ram, !book, !egtb, !stats. For hints in casual games: firsthint, secondhint, etc.'

                    if len(message) > 140:
                        message = message[:137] + "..."
                    result = await self.api.send_chat_message(self.game_info.id_, chat_message.room, message)
                except Exception as e:
                    print(f"Error sending help message: {e}")
                    await self.api.send_chat_message(self.game_info.id_, chat_message.room, "Supported commands: !help, !game, !opening, !eval, !name, !motor, !cpu, !ram, !draw")
            case 'hint':
                if self.game_info.rated:
                    await self.api.send_chat_message(self.game_info.id_, chat_message.room,
                                                     "Hints are only available in casual games.")
                    return
                
                opponent_is_bot = (self.game_info.white_title == 'BOT' and self.game_info.black_title == 'BOT')
                if opponent_is_bot:
                    await self.api.send_chat_message(self.game_info.id_, chat_message.room,
                                                     "Hints are only available against human opponents.")
                    return
                
                if chat_message.room not in ['player', 'spectator']:
                    await self.api.send_chat_message(self.game_info.id_, chat_message.room,
                                                     "Hints are only available in the player or spectator room.")
                    return
                
                if self.lichess_game.is_our_turn:
                    await self.api.send_chat_message(self.game_info.id_, chat_message.room,
                                                     "It's not your turn, so a hint wouldn't be helpful.")
                    return
                
                await self.api.send_chat_message(self.game_info.id_, chat_message.room,
                                                 "For hints, type: firsthint, secondhint, thirdhint, etc. in order.")
                return
            case 'game':
                try:
                    if self.lichess_game.scores:
                        score = self.lichess_game.scores[-1].relative
                        if score.is_mate():
                            mate_in = score.mate()
                            if mate_in > 0:
                                message = f"I'm winning and have a forced mate in {mate_in} moves!"
                            elif mate_in < 0:
                                message = f"I'm losing and facing mate in {abs(mate_in)} moves."
                            else:
                                message = "The game is drawn by mate."
                        else:
                            cp_score = score.score() / 100.0
                            if cp_score > 0.5:
                                message = f"I'm winning by {cp_score:.1f} pawns."
                            elif cp_score < -0.5:
                                message = f"I'm losing by {abs(cp_score):.1f} pawns."
                            else:
                                message = "The game is evenly balanced."
                    else:
                        message = "I'm currently analyzing the position."
                    
                    await self.api.send_chat_message(self.game_info.id_, chat_message.room, message)
                except Exception as e:
                    await self.api.send_chat_message(self.game_info.id_, chat_message.room,
                                                    "Analysis unavailable.")
            case 'ping':
                await self._handle_ping_command(chat_message)
            case _:
                pass

    async def _handle_hint_variation(self, chat_message: Chat_Message) -> None:
        if self.game_info.rated:
            await self.api.send_chat_message(self.game_info.id_, chat_message.room,
                                                     "Hints are only available in casual games.")
            return
        
        opponent_is_bot = (self.game_info.white_title == 'BOT' and self.game_info.black_title == 'BOT')
        if opponent_is_bot:
            await self.api.send_chat_message(self.game_info.id_, chat_message.room,
                                                     "Hints are only available against human opponents.")
            return
        
        if chat_message.room not in ['player', 'spectator']:
            await self.api.send_chat_message(self.game_info.id_, chat_message.room,
                                                     "Hints are only available in the player or spectator room.")
            return
        
        if self.lichess_game.is_our_turn:
            await self.api.send_chat_message(self.game_info.id_, chat_message.room,
                                                     "It's not your turn, so a hint wouldn't be helpful.")
            return
        
        hint_order = {
            'firsthint': 1,
            'secondhint': 2,
            'thirdhint': 3,
            'fourthhint': 4,
            'fifthhint': 5,
            'sixthhint': 6,
            'seventhhint': 7
        }
        
        requested_hint = hint_order[chat_message.text.lower()]
        
        if self.hint_counter >= 7:
            await self.api.send_chat_message(self.game_info.id_, chat_message.room,
                                                     "Your hints are over. I've already provided all 7 available hints for this game.")
            return
        
        if requested_hint != self.hint_counter + 1:
            if self.hint_counter + 1 > 7:
                await self.api.send_chat_message(self.game_info.id_, chat_message.room,
                                                         "Your hints are over. I've already provided all 7 available hints for this game.")
            else:
                await self.api.send_chat_message(self.game_info.id_, chat_message.room,
                                                         f"Request hints in order. Next hint is hint number {self.hint_counter + 1}.")
            return
        
        try:
            best_move, info = await self.lichess_game.engine.make_hint_move(
                self.lichess_game.board
            )
            move_san = self.lichess_game.board.san(best_move)
            message = f"Hint {requested_hint}: The suggested move is {move_san}"
            
            if 'score' in info:
                score = self.lichess_game._format_score(info['score'])
                message += f" with evaluation {score}"
            
            await self.api.send_chat_message(self.game_info.id_, chat_message.room, message)
            self.hint_counter = requested_hint
        except Exception as e:
            await self.api.send_chat_message(self.game_info.id_, chat_message.room,
                                                     "Hint unavailable.")

    async def _handle_ping_command(self, chat_message: Chat_Message) -> None:
        try:
            start_time = time.time()
            response = await self.api.get_account()
            end_time = time.time()
            
            ping_ms = round((end_time - start_time) * 1000)
            await self.api.send_chat_message(self.game_info.id_, chat_message.room, 
                                           f"Ping to Lichess: {ping_ms}ms")
        except Exception as e:
            await self.api.send_chat_message(self.game_info.id_, chat_message.room,
                                           "Could not measure ping to Lichess.")

    async def _send_last_message(self, room: str) -> None:
        last_message = self.lichess_game.last_message.replace('Engine', 'Evaluation')
        last_message = ' '.join(last_message.split())

        if room == 'spectator':
            last_message = self._append_pv(last_message)

        await self.api.send_chat_message(self.game_info.id_, room, last_message)

    def _get_cpu(self) -> str:
        cpu = ''
        if os.path.exists('/proc/cpuinfo'):
            with open('/proc/cpuinfo', encoding='utf-8') as cpuinfo:
                while line := cpuinfo.readline():
                    if line.startswith('model name'):
                        cpu = line.split(': ')[1]
                        cpu = cpu.replace('(R)', '')
                        cpu = cpu.replace('(TM)', '')

                        if len(cpu.split()) > 1:
                            return cpu

        if processor := platform.processor():
            cpu = processor.split()[0]
            cpu = cpu.replace('GenuineIntel', 'Intel')

        cores = psutil.cpu_count(logical=False)
        threads = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq().max / 1000

        return f'{cpu} {cores}c/{threads}t @ {cpu_freq:.2f}GHz'

    def _get_ram(self) -> str:
        mem_bytes = psutil.virtual_memory().total
        mem_gib = mem_bytes / (1024.**3)

        return f'{mem_gib:.1f} GiB'

    def _get_draw_message(self, config: Config) -> str:
        if not config.offer_draw.enabled:
            return 'This bot will neither accept nor offer draws.'

        max_score = config.offer_draw.score / 100

        return (f'The bot offers draw at move {config.offer_draw.min_game_length} or later '
                f'if the eval is within +{max_score:.2f} to -{max_score:.2f} for the last '
                f'{config.offer_draw.consecutive_moves} moves.')

    def _get_name_message(self, version: str) -> str:
        return (f'{self.username} running {self.lichess_game.engine.name} (BotLi {version})')

    def _format_message(self, message: str | None) -> str | None:
        if not message:
            return

        opponent_username = self.game_info.black_name if self.lichess_game.is_white else self.game_info.white_name
        mapping = defaultdict(str, {'opponent': opponent_username, 'me': self.username,
                                    'engine': self.lichess_game.engine.name, 'cpu': self.cpu_message,
                                    'ram': self.ram_message})
        return message.format_map(mapping)

    def _append_pv(self, initial_message: str = '') -> str:
        if len(self.lichess_game.last_pv) < 2:
            return initial_message

        if initial_message:
            initial_message += ' '

        if self.lichess_game.is_our_turn:
            board = self.lichess_game.board.copy(stack=1)
            board.pop()
        else:
            board = self.lichess_game.board.copy(stack=False)

        if board.turn:
            initial_message += 'PV:'
        else:
            initial_message += f'PV: {board.fullmove_number}...'

        final_message = initial_message
        for move in self.lichess_game.last_pv[1:]:
            if board.turn:
                initial_message += f' {board.fullmove_number}.'
            initial_message += f' {board.san(move)}'
            if len(initial_message) > 140:
                break
            board.push(move)
            final_message = initial_message

        return final_message


