from __future__ import annotations
from dotenv import load_dotenv
load_dotenv()

import sys
from decimal import Decimal

from PySide6.QtCore import Qt, QCoreApplication, QObject, Signal, Slot, QThread
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
)
from PySide6.QtGui import QIcon

from data.models import init_db
from data.repositories import load_share_purchases_as_rows
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
        exit_button = QPushButton("Exit", self)

        show_analysis_button.clicked.connect(self._open_analysis)
        exit_button.clicked.connect(QCoreApplication.quit)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(show_analysis_button)
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

    def _open_analysis(self) -> None:
        if self._analysis_window is None:
            self._analysis_window = AnalysisWindow()
        self._analysis_window.show()
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

        self.summary_label = QLabel(self)
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        top_bar = QHBoxLayout()
        top_bar.addWidget(self.refresh_button)
        top_bar.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(top_bar)
        layout.addWidget(self.table)
        layout.addWidget(self.summary_label)

        # Track worker/thread to prevent GC
        self._thread: QThread | None = None
        self._worker: AnalysisWorker | None = None

        # Initial load
        self.refresh_analysis()

    def refresh_analysis(self) -> None:
        purchases = load_share_purchases_as_rows()
        if not purchases:
            self.table.setRowCount(0)
            self.summary_label.setText("No purchases found. Add purchases to see analysis.")
            return

        earliest_date = purchases[0]["purchase_date"]

        # Disable button during work
        self.refresh_button.setEnabled(False)

        # Create thread & worker
        self._thread = QThread(self)
        self._worker = AnalysisWorker(purchases, earliest_date)
        self._worker.moveToThread(self._thread)

        # Wire signals
        self._thread.started.connect(self._worker.run)
        self._worker.success.connect(self._update_ui_from_result)
        self._worker.error.connect(lambda msg: QMessageBox.critical(self, "Analysis Error", msg))
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(lambda: self.refresh_button.setEnabled(True))

        self._thread.start()

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


if __name__ == "__main__":
    init_db()

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("assets/icon.png"))
    chooser = InitialWindow()
    chooser.show()
    sys.exit(app.exec())