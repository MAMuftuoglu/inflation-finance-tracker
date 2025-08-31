from __future__ import annotations
from dotenv import load_dotenv
load_dotenv()

import sys
from decimal import Decimal
from datetime import date

from PySide6.QtCore import Qt, QCoreApplication, QObject, Signal, Slot, QThread, QDate
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QLineEdit,
    QFormLayout,
    QDateEdit,
    QSpinBox,
    QDoubleSpinBox,
    QComboBox,
    QProgressBar,
)
from PySide6.QtGui import QIcon

from data.models import init_db
from data.repositories import load_share_purchases_as_rows, add_share_purchase
from infra.cpi_data_provider import BlsCpiDataProvider
from services.investment_service import run_investment_analysis


def format_currency(value: Decimal) -> str:
    try:
        return f"${Decimal(value):,.2f}"
    except Exception:
        return str(value)

class InitialWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Financial Report")
        self.resize(480, 240)

        title_label = QLabel("Financial Report", self)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle_label = QLabel("Choose an option to continue", self)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        show_analysis_button = QPushButton("Show Analysis", self)
        add_shares_button = QPushButton("Add Shares", self)
        exit_button = QPushButton("Exit", self)

        show_analysis_button.clicked.connect(self._open_analysis)
        add_shares_button.clicked.connect(self._open_add_shares)
        exit_button.clicked.connect(QCoreApplication.quit)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(show_analysis_button)
        buttons.addSpacing(12)
        buttons.addWidget(add_shares_button)
        buttons.addSpacing(12)
        buttons.addWidget(exit_button)
        buttons.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        layout.addStretch(1)
        layout.addLayout(buttons)
        layout.addStretch(2)

        self._analysis_window: AnalysisWindow | None = None
        self._add_shares_window: AddSharesWindow | None = None

    def _open_analysis(self) -> None:
        if self._analysis_window is None:
            self._analysis_window = AnalysisWindow()
            self._analysis_window.set_parent_window(self)
        self._analysis_window.show()
        self.hide()

    def _open_add_shares(self) -> None:
        if self._add_shares_window is None:
            self._add_shares_window = AddSharesWindow()
            self._add_shares_window.set_parent_window(self)
        self._add_shares_window.show()
        self.hide()

class AnalysisWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Investment Analysis")
        self.resize(900, 600)

        self.table = QTableWidget(self)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Symbol",
            "Invested (Nominal)",
            "Invested (Real)",
            "Current Value",
            "Profit (Nominal)",
            "Profit (Real)",
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)

        self.refresh_button = QPushButton("Refresh Analysis", self)
        self.refresh_button.clicked.connect(self.refresh_analysis)

        self.back_button = QPushButton("Back to Main Menu", self)
        self.back_button.clicked.connect(self._go_back)

        # Loading indicator
        self.loading_label = QLabel("Loading analysis...", self)
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("color: #666; font-style: italic;")
        self.loading_label.hide()

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.hide()

        self.summary_label = QLabel(self)
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        top_bar = QHBoxLayout()
        top_bar.addWidget(self.refresh_button)
        top_bar.addWidget(self.back_button)
        top_bar.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(top_bar)
        layout.addWidget(self.loading_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.table)
        layout.addWidget(self.summary_label)

        # Track worker/thread to prevent GC
        self._thread: QThread | None = None
        self._worker: AnalysisWorker | None = None
        self._parent_window = None

        # Initial load
        self.refresh_analysis()

    def set_parent_window(self, parent_window):
        self._parent_window = parent_window

    def _go_back(self) -> None:
        if self._parent_window:
            self._parent_window.show()
        self.hide()

    def _set_loading_state(self, loading: bool) -> None:
        """Set the UI to loading or normal state."""
        if loading:
            # Show loading indicators
            self.loading_label.show()
            self.progress_bar.show()
            # Disable interactive elements
            self.refresh_button.setEnabled(False)
            self.back_button.setEnabled(False)
            self.table.setEnabled(False)
            # Clear table and show loading message
            self.table.setRowCount(0)
            self.summary_label.setText("Loading analysis... Please wait.")
        else:
            # Hide loading indicators
            self.loading_label.hide()
            self.progress_bar.hide()
            # Re-enable interactive elements
            self.refresh_button.setEnabled(True)
            self.back_button.setEnabled(True)
            self.table.setEnabled(True)

    def refresh_analysis(self) -> None:
        purchases = load_share_purchases_as_rows()
        if not purchases:
            self.table.setRowCount(0)
            self.summary_label.setText("No purchases found. Add purchases to see analysis.")
            return

        earliest_date = purchases[0]["purchase_date"]

        # Set loading state
        self._set_loading_state(True)

        # Create thread & worker
        self._thread = QThread(self)
        self._worker = AnalysisWorker(purchases, earliest_date)
        self._worker.moveToThread(self._thread)

        # Wire signals
        self._thread.started.connect(self._worker.run)
        self._worker.success.connect(self._update_ui_from_result)
        self._worker.error.connect(self._handle_analysis_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(lambda: self._set_loading_state(False))

        self._thread.start()

    @Slot(str)
    def _handle_analysis_error(self, error_message: str) -> None:
        """Handle analysis errors and reset loading state."""
        QMessageBox.critical(self, "Analysis Error", error_message)
        self._set_loading_state(False)

    @Slot(list, object)
    def _update_ui_from_result(self, company_results, totals) -> None:
        self.table.setRowCount(len(company_results))
        for row_index, company in enumerate(company_results):
            self.table.setItem(row_index, 0, QTableWidgetItem(company.name))
            self.table.setItem(row_index, 1, QTableWidgetItem(format_currency(company.total_nominal_invested)))
            self.table.setItem(row_index, 2, QTableWidgetItem(format_currency(company.total_real_invested)))
            self.table.setItem(row_index, 3, QTableWidgetItem(format_currency(company.total_current_value)))
            self.table.setItem(row_index, 4, QTableWidgetItem(format_currency(company.total_nominal_profit)))
            self.table.setItem(row_index, 5, QTableWidgetItem(format_currency(company.total_real_profit)))

        totals_text = (
            f"Portfolio Totals:\n"
            f"  Invested (Nominal): {format_currency(totals.total_nominal_invested)}\n"
            f"  Invested (Real):    {format_currency(totals.total_real_invested)}\n"
            f"  Current Value:      {format_currency(totals.total_current_value)}\n"
            f"  Profit (Nominal):   {format_currency(totals.total_nominal_profit)}\n"
            f"  Profit (Real):      {format_currency(totals.total_real_profit)}"
        )
        self.summary_label.setText(totals_text)


class AnalysisWorker(QObject):
    finished = Signal()
    success = Signal(list, object)
    error = Signal(str)

    def __init__(self, purchases: list, earliest_date: str) -> None:
        super().__init__()
        self._purchases = purchases
        self._earliest_date = earliest_date

    @Slot()
    def run(self) -> None:
        try:
            cpi_data_provider = BlsCpiDataProvider()
            company_results, totals = run_investment_analysis(
                purchase_rows=self._purchases,
                initial_year=self._earliest_date,
                cpi_data_provider=cpi_data_provider,
            )
            self.success.emit(company_results, totals)
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.finished.emit()


class AddSharesWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Add Shares")
        self.resize(400, 300)

        # Create form widgets
        self.symbol_edit = QLineEdit(self)
        self.symbol_edit.setPlaceholderText("e.g., AAPL")
        
        self.market_edit = QLineEdit(self)
        self.market_edit.setPlaceholderText("e.g., NASDAQ, NYSE, LSE, TSE")
        
        self.quantity_spin = QDoubleSpinBox(self)
        self.quantity_spin.setDecimals(6)
        self.quantity_spin.setRange(0.000001, 999999.999999)
        self.quantity_spin.setValue(1.0)
        
        self.cost_spin = QDoubleSpinBox(self)
        self.cost_spin.setDecimals(2)
        self.cost_spin.setRange(0.01, 999999.99)
        self.cost_spin.setValue(100.00)
        self.cost_spin.setPrefix("$")
        
        self.date_edit = QDateEdit(self)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)

        # Create form layout
        form_layout = QFormLayout()
        form_layout.addRow("Symbol:", self.symbol_edit)
        form_layout.addRow("Market:", self.market_edit)
        form_layout.addRow("Quantity:", self.quantity_spin)
        form_layout.addRow("Cost per Share:", self.cost_spin)
        form_layout.addRow("Purchase Date:", self.date_edit)

        # Create buttons
        add_button = QPushButton("Add Share Purchase", self)
        add_button.clicked.connect(self._add_share)
        
        back_button = QPushButton("Back to Main Menu", self)
        back_button.clicked.connect(self._go_back)

        button_layout = QHBoxLayout()
        button_layout.addWidget(add_button)
        button_layout.addWidget(back_button)

        # Main layout
        layout = QVBoxLayout(self)
        layout.addLayout(form_layout)
        layout.addStretch(1)
        layout.addLayout(button_layout)

        self._parent_window = None

    def set_parent_window(self, parent_window):
        self._parent_window = parent_window

    def _add_share(self) -> None:
        symbol = self.symbol_edit.text().strip().upper()
        market = self.market_edit.text().strip()
        quantity = Decimal(str(self.quantity_spin.value()))
        cost = Decimal(str(self.cost_spin.value()))
        qdate = self.date_edit.date()
        purchase_date = date(qdate.year(), qdate.month(), qdate.day())

        if not symbol:
            QMessageBox.warning(self, "Validation Error", "Please enter a symbol.")
            return

        if not market:
            QMessageBox.warning(self, "Validation Error", "Please enter a market.")
            return

        if quantity <= 0:
            QMessageBox.warning(self, "Validation Error", "Quantity must be greater than 0.")
            return

        if cost <= 0:
            QMessageBox.warning(self, "Validation Error", "Cost must be greater than 0.")
            return

        # Add the share purchase
        result = add_share_purchase(
            symbol=symbol,
            market=market,
            quantity=quantity,
            cost=cost,
            purchase_date=purchase_date,
        )

        if result["success"]:
            QMessageBox.information(
                self,
                "Success",
                f"Share purchase added successfully!\n\n"
                f"Symbol: {result['symbol']}\n"
                f"Market: {result['market']}\n"
                f"Quantity: {result['quantity']}\n"
                f"Cost: ${result['cost']}\n"
                f"Date: {result['purchase_date']}\n"
                f"Market mapping: {result['market_action']}"
            )
            # Clear the form
            self.symbol_edit.clear()
            self.market_edit.clear()
            self.quantity_spin.setValue(1.0)
            self.cost_spin.setValue(100.00)
            self.date_edit.setDate(QDate.currentDate())
        else:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to add share purchase:\n{result['error']}"
            )

    def _go_back(self) -> None:
        if self._parent_window:
            self._parent_window.show()
        self.hide()


if __name__ == "__main__":
    init_db()

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("assets/icon.png"))
    chooser = InitialWindow()
    chooser.show()
    sys.exit(app.exec())