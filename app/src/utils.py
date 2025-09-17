"""
Утилиты для автоматического пересчета коэффициентов и других операций
"""
import math
from typing import List, Dict
from src.database import (
    get_event_by_id, DATABASE_URL, get_db, Outcome, Event, Bet,
    EventStatus, BetStatus
)
from config.settings import HOUSE_EDGE, DEFAULT_ODDS

def calculate_probability_from_odds(odds: float) -> float:
    """Вычислить вероятность из коэффициента"""
    return 1.0 / odds

def calculate_odds_from_probability(probability: float, house_edge: float = HOUSE_EDGE) -> float:
    """Вычислить коэффициент из вероятности с учетом комиссии дома"""
    if probability <= 0:
        return DEFAULT_ODDS
    
    # Применяем комиссию дома
    adjusted_probability = probability * (1 + house_edge)
    
    # Убеждаемся, что вероятность не превышает 1
    if adjusted_probability >= 1:
        adjusted_probability = 0.95
    
    return 1.0 / adjusted_probability

def calculate_market_probabilities(outcomes_data: List[Dict]) -> Dict[int, float]:
    """
    Вычислить рыночные вероятности на основе объемов ставок
    
    Args:
        outcomes_data: Список словарей с данными исходов
                      [{'id': int, 'total_amount': float, 'current_odds': float}, ...]
    
    Returns:
        Словарь {outcome_id: probability}
    """
    total_market_amount = sum(outcome['total_amount'] for outcome in outcomes_data)
    
    if total_market_amount == 0:
        # Если ставок нет, используем равные вероятности
        equal_probability = 1.0 / len(outcomes_data)
        return {outcome['id']: equal_probability for outcome in outcomes_data}
    
    # Вычисляем вероятности на основе объемов ставок
    probabilities = {}
    
    for outcome in outcomes_data:
        # Базовая вероятность на основе объема ставок
        volume_probability = outcome['total_amount'] / total_market_amount
        
        # Текущая вероятность на основе коэффициента
        current_probability = calculate_probability_from_odds(outcome['current_odds'])
        
        # Комбинируем обе вероятности (70% объем, 30% текущий коэффициент)
        combined_probability = 0.7 * volume_probability + 0.3 * current_probability
        
        probabilities[outcome['id']] = combined_probability
    
    # Нормализуем вероятности, чтобы их сумма была 1
    total_probability = sum(probabilities.values())
    if total_probability > 0:
        for outcome_id in probabilities:
            probabilities[outcome_id] /= total_probability
    
    return probabilities

def calculate_kelly_criterion(probability: float, odds: float, bankroll: float) -> float:
    """
    Вычислить оптимальный размер ставки по критерию Келли
    
    Args:
        probability: Вероятность выигрыша
        odds: Коэффициент
        bankroll: Размер банкролла
    
    Returns:
        Рекомендуемый размер ставки
    """
    if probability <= 0 or odds <= 1:
        return 0
    
    # Формула Келли: f = (bp - q) / b
    # где b = odds - 1, p = probability, q = 1 - probability
    b = odds - 1
    p = probability
    q = 1 - probability
    
    kelly_fraction = (b * p - q) / b
    
    # Ограничиваем максимальную долю банкролла
    kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Максимум 25% банкролла
    
    return kelly_fraction * bankroll

async def recalculate_event_odds(event_id: int) -> bool:
    """
    Пересчитать коэффициенты для события на основе текущих ставок
    
    Args:
        event_id: ID события
    
    Returns:
        True если пересчет успешен, False иначе
    """
    try:
        if DATABASE_URL.startswith('sqlite'):
            db = get_db()
            
            # Получаем событие с исходами
            event = db.query(Event).filter(Event.id == event_id).first()
            if not event or event.status != EventStatus.UPCOMING:
                return False
            
            # Собираем данные по исходам
            outcomes_data = []
            for outcome in event.outcomes:
                outcomes_data.append({
                    'id': outcome.id,
                    'total_amount': outcome.total_amount,
                    'current_odds': outcome.odds
                })
            
            if not outcomes_data:
                return False
            
            # Вычисляем новые вероятности
            new_probabilities = calculate_market_probabilities(outcomes_data)
            
            # Обновляем коэффициенты
            for outcome in event.outcomes:
                if outcome.id in new_probabilities:
                    new_probability = new_probabilities[outcome.id]
                    new_odds = calculate_odds_from_probability(new_probability)
                    
                    # Применяем сглаживание (70% новый коэффициент, 30% старый)
                    smoothed_odds = 0.7 * new_odds + 0.3 * outcome.odds
                    
                    # Ограничиваем минимальный и максимальный коэффициенты
                    smoothed_odds = max(1.01, min(smoothed_odds, 50.0))
                    
                    outcome.odds = round(smoothed_odds, 2)
            
            db.commit()
            return True
            
    except Exception as e:
        print(f"Ошибка при пересчете коэффициентов: {e}")
        return False

async def auto_recalculate_all_events():
    """Автоматически пересчитать коэффициенты для всех активных событий"""
    try:
        if DATABASE_URL.startswith('sqlite'):
            db = get_db()
            
            # Получаем все активные события
            active_events = db.query(Event).filter(
                Event.status == EventStatus.UPCOMING
            ).all()
            
            for event in active_events:
                await recalculate_event_odds(event.id)
                
    except Exception as e:
        print(f"Ошибка при автоматическом пересчете: {e}")

def calculate_arbitrage_opportunities(outcomes: List[Dict]) -> Dict:
    """
    Вычислить арбитражные возможности
    
    Args:
        outcomes: Список исходов с коэффициентами
                 [{'title': str, 'odds': float}, ...]
    
    Returns:
        Словарь с информацией об арбитраже
    """
    if len(outcomes) < 2:
        return {'is_arbitrage': False}
    
    # Вычисляем сумму обратных коэффициентов
    inverse_sum = sum(1.0 / outcome['odds'] for outcome in outcomes)
    
    # Если сумма меньше 1, есть арбитражная возможность
    is_arbitrage = inverse_sum < 1.0
    
    if is_arbitrage:
        # Вычисляем оптимальные доли ставок
        total_stake = 100  # Условная сумма
        stakes = []
        
        for outcome in outcomes:
            stake = (total_stake / outcome['odds']) / inverse_sum
            stakes.append({
                'outcome': outcome['title'],
                'stake': round(stake, 2),
                'odds': outcome['odds']
            })
        
        profit_margin = (1.0 - inverse_sum) * 100
        
        return {
            'is_arbitrage': True,
            'profit_margin': round(profit_margin, 2),
            'stakes': stakes,
            'total_stake': total_stake
        }
    
    return {
        'is_arbitrage': False,
        'margin': round((inverse_sum - 1.0) * 100, 2)
    }

def calculate_expected_value(probability: float, odds: float, stake: float) -> float:
    """
    Вычислить ожидаемую стоимость ставки
    
    Args:
        probability: Вероятность выигрыша
        odds: Коэффициент
        stake: Размер ставки
    
    Returns:
        Ожидаемая стоимость
    """
    win_amount = stake * odds
    lose_amount = stake
    
    expected_value = probability * win_amount - (1 - probability) * lose_amount
    return expected_value

def get_betting_recommendation(probability: float, odds: float, user_balance: float) -> Dict:
    """
    Получить рекомендацию по ставке
    
    Args:
        probability: Предполагаемая вероятность выигрыша
        odds: Коэффициент
        user_balance: Баланс пользователя
    
    Returns:
        Словарь с рекомендацией
    """
    # Вычисляем ожидаемую стоимость
    expected_value = calculate_expected_value(probability, odds, 1.0)  # На единицу ставки
    
    # Вычисляем рекомендуемый размер по Келли
    kelly_stake = calculate_kelly_criterion(probability, odds, user_balance)
    
    # Определяем рекомендацию
    if expected_value > 0:
        if kelly_stake > 0:
            recommendation = "РЕКОМЕНДУЕТСЯ"
            confidence = min(100, int(expected_value * 100))
        else:
            recommendation = "ОСТОРОЖНО"
            confidence = 30
    else:
        recommendation = "НЕ РЕКОМЕНДУЕТСЯ"
        confidence = 0
    
    return {
        'recommendation': recommendation,
        'confidence': confidence,
        'expected_value': round(expected_value, 3),
        'kelly_stake': round(kelly_stake, 2),
        'kelly_percentage': round((kelly_stake / user_balance) * 100, 1) if user_balance > 0 else 0
    }

def format_odds_change(old_odds: float, new_odds: float) -> str:
    """Форматировать изменение коэффициентов"""
    if old_odds == new_odds:
        return f"{new_odds:.2f}"
    
    change = new_odds - old_odds
    direction = "📈" if change > 0 else "📉"
    
    return f"{new_odds:.2f} {direction} ({change:+.2f})"

def calculate_payout_simulation(event_outcomes: List[Dict], total_pool: float) -> Dict:
    """
    Симуляция выплат для разных исходов события
    
    Args:
        event_outcomes: Список исходов с данными о ставках
        total_pool: Общий пул ставок
    
    Returns:
        Словарь с симуляцией выплат
    """
    simulation = {}
    
    for outcome in event_outcomes:
        outcome_id = outcome['id']
        outcome_title = outcome['title']
        outcome_bets = outcome['bets']  # Список ставок на этот исход
        
        # Вычисляем общие выплаты если этот исход выиграет
        total_payout = sum(bet['amount'] * bet['odds'] for bet in outcome_bets)
        
        # Прибыль/убыток дома
        house_profit = total_pool - total_payout
        
        simulation[outcome_id] = {
            'title': outcome_title,
            'total_payout': round(total_payout, 2),
            'house_profit': round(house_profit, 2),
            'house_margin': round((house_profit / total_pool) * 100, 1) if total_pool > 0 else 0,
            'winning_bets': len(outcome_bets)
        }
    
    return simulation

# Функция для периодического обновления коэффициентов
async def scheduled_odds_update():
    """Запланированное обновление коэффициентов (вызывается по расписанию)"""
    print("Запуск автоматического пересчета коэффициентов...")
    await auto_recalculate_all_events()
    print("Пересчет коэффициентов завершен")
